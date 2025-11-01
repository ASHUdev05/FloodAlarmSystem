# --- Imports ---
import os
import io
import time
import threading
import requests
from datetime import datetime
import numpy as np
import tensorflow as tf
from tensorflow.keras.models import load_model
from tensorflow.keras import backend as K
from fastapi import FastAPI, UploadFile, File, Query
from fastapi.responses import JSONResponse
from PIL import Image
import uvicorn

# --- Config ---
MODEL_PATH = "flood_model.h5"
IMG_HEIGHT = 256
IMG_WIDTH = 256
FETCH_INTERVAL = 60  # seconds

# Default coordinates (New Delhi)
LATITUDE = 21.9497
LONGITUDE = 89.1833

latest_result = None

# --- Dice functions ---
def dice_coefficient(y_true, y_pred, smooth=1):
    y_true_f = K.flatten(y_true)
    y_pred_f = K.flatten(y_pred)
    intersection = K.sum(y_true_f * y_pred_f)
    return (2. * intersection + smooth) / (K.sum(y_true_f) + K.sum(y_pred_f) + smooth)

def dice_loss(y_true, y_pred):
    return 1 - dice_coefficient(y_true, y_pred)

# --- Load Model ---
print(f"Loading model from {MODEL_PATH}...")
model = load_model(MODEL_PATH, custom_objects={'dice_loss': dice_loss, 'dice_coefficient': dice_coefficient})
print("✅ Model loaded successfully!")

# --- FastAPI App ---
app = FastAPI(title="Flood Segmentation API (Location Aware)")

# --- Image Preprocessing ---
def preprocess_image(image_bytes: bytes) -> np.ndarray:
    img = Image.open(io.BytesIO(image_bytes)).convert('RGB')
    img = img.resize((IMG_HEIGHT, IMG_WIDTH), Image.Resampling.LANCZOS)
    img_array = np.array(img) / 255.0
    return np.expand_dims(img_array, axis=0)

# --- Build Satellite Image URL ---
def build_satellite_url(lat, lon, date=None):
    """Use NASA Worldview Snapshot API for real satellite imagery."""
    if date is None:
        date = datetime.utcnow().strftime("%Y-%m-%d")

    # Define a small bounding box (about ~40km area)
    min_lon, max_lon = lon - 0.2, lon + 0.2
    min_lat, max_lat = lat - 0.2, lat + 0.2

    return (
        "https://wvs.earthdata.nasa.gov/api/v1/snapshot?"
        f"REQUEST=GetSnapshot&TIME={date}"
        "&BBOX={},{},{},{}"
        "&CRS=EPSG:4326&LAYERS=VIIRS_SNPP_CorrectedReflectance_TrueColor"
        "&FORMAT=image/jpeg&WIDTH=512&HEIGHT=512"
    ).format(min_lon, min_lat, max_lon, max_lat)

# --- Live Fetch + Predict Thread ---
def fetch_and_predict_loop():
    global latest_result
    while True:
        try:
            url = build_satellite_url(LATITUDE, LONGITUDE)
            print(f"[{datetime.now()}] Fetching satellite image for ({LATITUDE}, {LONGITUDE})")

            r = requests.get(url)
            if r.status_code == 200 and "image" in r.headers.get("content-type", ""):
                img_array = preprocess_image(r.content)
                prediction = model.predict(img_array)[0, :, :, 0]

                flood_pct = float(np.sum(prediction > 0.5) / (IMG_HEIGHT * IMG_WIDTH) * 100)
                flood_detected = bool(flood_pct > 50)

                latest_result = {
                    "timestamp": datetime.now().isoformat(),
                    "latitude": LATITUDE,
                    "longitude": LONGITUDE,
                    "flood_detected": flood_detected,
                    "flood_percentage": round(flood_pct, 2)
                }

                print(f"✅ Live Feed ({LATITUDE},{LONGITUDE}): {flood_pct:.2f}% flooded")
            else:
                print(f"⚠️ Failed to fetch image: {r.status_code} ({r.headers.get('content-type')})")

            time.sleep(FETCH_INTERVAL)
        except Exception as e:
            print("❌ Live feed error:", e)
            time.sleep(FETCH_INTERVAL)

@app.on_event("startup")
def start_live_feed_thread():
    threading.Thread(target=fetch_and_predict_loop, daemon=True).start()
    print("🚀 Live feed thread started!")

# --- API Endpoints ---
@app.get("/")
def root():
    return {"status": "ok", "message": "Welcome to the Flood Segmentation API (Location Aware)!"}

@app.get("/set_location")
def set_location(lat: float = Query(...), lon: float = Query(...)):
    """Change live feed location dynamically."""
    global LATITUDE, LONGITUDE
    LATITUDE, LONGITUDE = lat, lon
    return {
        "message": "✅ Location updated successfully!",
        "latitude": lat,
        "longitude": lon
    }

@app.get("/live")
def get_live_data():
    return latest_result or {"message": "Waiting for first live prediction..."}

# --- Prediction Endpoint ---
@app.post("/predict")
async def predict_flood(file: UploadFile = File(...)):
    try:
        image_bytes = await file.read()
        preprocessed = preprocess_image(image_bytes)
        prediction = model.predict(preprocessed)[0, :, :, 0]

        flood_pct = float(np.sum(prediction > 0.5) / (IMG_HEIGHT * IMG_WIDTH) * 100)
        flood_detected = bool(flood_pct > 50)

        return {
            "filename": file.filename,
            "flood_detected": flood_detected,
            "flood_percentage": round(flood_pct, 2)
        }

    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})

# --- Run App ---
if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
