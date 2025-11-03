import io
import os
import requests
from datetime import datetime, timezone, timedelta  # <-- 1. Import timedelta
import numpy as np
import tensorflow as tf
from tensorflow.keras import backend as K
from PIL import Image

# --- Model Config ---
# Get the absolute path to the directory this file is in
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
# Join it with the model file name
MODEL_PATH = os.path.join(BASE_DIR, "flood_model.h5")

IMG_HEIGHT = 256
IMG_WIDTH = 256
# 2. FIX: Set minimum size just above the "No Data" size (1820 bytes)
MIN_IMAGE_SIZE_BYTES = 2000  # 2 KB (was 3000)

# --- Dice functions ---
def dice_coefficient(y_true, y_pred, smooth=1):
    y_true_f = K.flatten(y_true)
    y_pred_f = K.flatten(y_pred)
    intersection = K.sum(y_true_f * y_pred_f)
    return (2. * intersection + smooth) / (K.sum(y_true_f) + K.sum(y_pred_f) + smooth)

def dice_loss(y_true, y_pred):
    return 1 - dice_coefficient(y_true, y_pred)

# --- Load Model (function) ---
def load_prediction_model():
    print(f"Loading model from {MODEL_PATH}...")
    if not os.path.exists(MODEL_PATH):
        print(f"ERROR: Model file not found at {MODEL_PATH}")
        return None
    try:
        # Load model without compiling optimizer, we only need inference
        model = tf.keras.models.load_model(
            MODEL_PATH,
            custom_objects={'dice_loss': dice_loss, 'dice_coefficient': dice_coefficient},
            compile=False
        )
        print("✅ Model loaded successfully!")
        return model
    except Exception as e:
        print(f"CRITICAL: Failed to load model: {e}")
        return None

# --- Image Preprocessing ---
def preprocess_image(image_bytes: bytes) -> np.ndarray:
    img = Image.open(io.BytesIO(image_bytes)).convert('RGB')
    img = img.resize((IMG_HEIGHT, IMG_WIDTH), Image.Resampling.LANCZOS)
    img_array = np.array(img) / 255.0
    return np.expand_dims(img_array, axis=0)

# --- Build Satellite URL ---
def build_satellite_url(lat, lon, date=None):
    if date is None:
        # 3. FIX: Use *2 days ago* date to ensure data is processed
        date = (datetime.now(timezone.utc) - timedelta(days=2)).strftime("%Y-%m-%d")

    min_lon, max_lon = lon - 0.2, lon + 0.2
    min_lat, max_lat = lat - 0.2, lat + 0.2

    return (
        "https://wvs.earthdata.nasa.gov/api/v1/snapshot?"
        f"REQUEST=GetSnapshot&TIME={date}"
        "&BBOX={},{},{},{}"
        "&CRS=EPSG:4326&LAYERS=VIIRS_SNPP_CorrectedReflectance_TrueColor"
        "&FORMAT=image/jpeg&WIDTH=512&HEIGHT=512"
    ).format(min_lon, min_lat, max_lon, max_lat)

# --- Prediction Function ---
def get_prediction(model, lat, lon):
    try:
        # Build URL for *2 days ago* to ensure data is available
        url = build_satellite_url(lat, lon)
        print(f"Fetching: {url}") # Add logging
        r = requests.get(url)

        if r.status_code == 200 and "image" in r.headers.get("content-type", ""):

            # 4. NEW FIX: Check the size of the image.
            image_size = len(r.content)
            if image_size < MIN_IMAGE_SIZE_BYTES:
                print(f"⚠️ Fetched image for ({lat},{lon}) is too small ({image_size} bytes). Assuming 'No Data'.")
                # Return 0% flood for "No Data"
                return 0.0
            # --- END FIX ---

            img_array = preprocess_image(r.content)

            # Run prediction
            prediction = model.predict(img_array)[0, :, :, 0]

            # Calculate percentage
            flood_pct = float(np.sum(prediction > 0.5) / (IMG_HEIGHT * IMG_WIDTH) * 100)
            print(f"✅ Prediction for ({lat},{lon}): {flood_pct:.2f}%") # Add logging
            return round(flood_pct, 2)
        else:
            print(f"⚠️ Failed to fetch image for ({lat},{lon}): {r.status_code} {r.headers.get('content-type')}")
            return None
    except Exception as e:
        print(f"❌ Prediction error for ({lat},{lon}): {e}")
        return None

