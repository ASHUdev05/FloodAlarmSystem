import io
import os
import requests
from datetime import datetime, timezone
import numpy as np
import tensorflow as tf
from tensorflow.keras import backend as K
from PIL import Image

# --- Model Config ---
IMG_HEIGHT = 256
IMG_WIDTH = 256
# 2. MAKE THE PATH DYNAMIC AND ROBUST
# This gets the absolute path of the directory this file (prediction_utils.py) is in
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
# This joins that directory path with the model filename
MODEL_PATH = os.path.join(BASE_DIR, "flood_model.h5")

# --- Dice functions (copied from your old main.py) ---
def dice_coefficient(y_true, y_pred, smooth=1):
    y_true_f = K.flatten(y_true)
    y_pred_f = K.flatten(y_pred)
    intersection = K.sum(y_true_f * y_pred_f)
    return (2. * intersection + smooth) / (K.sum(y_true_f) + K.sum(y_pred_f) + smooth)

def dice_loss(y_true, y_pred):
    return 1 - dice_coefficient(y_true, y_pred)

# --- Load Model (function) ---
def load_prediction_model():
    print(f"Loading model from {MODEL_PATH}...") # This will now print the full, correct path
    model = tf.keras.models.load_model(
        MODEL_PATH,
        custom_objects={'dice_loss': dice_loss, 'dice_coefficient': dice_coefficient}
    )
    print("✅ Model loaded successfully!")
    return model

# --- Image Preprocessing (copied from your old main.py) ---
def preprocess_image(image_bytes: bytes) -> np.ndarray:
    img = Image.open(io.BytesIO(image_bytes)).convert('RGB')
    img = img.resize((IMG_HEIGHT, IMG_WIDTH), Image.Resampling.LANCZOS)
    img_array = np.array(img) / 255.0
    return np.expand_dims(img_array, axis=0)

# --- Build Satellite URL (copied from your old main.py) ---
def build_satellite_url(lat, lon, date=None):
    if date is None:
        # Use timezone-aware UTC time
        date = datetime.now(timezone.utc).strftime("%Y-%m-%d")  
    
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
        url = build_satellite_url(lat, lon)
        r = requests.get(url)

        if r.status_code == 200 and "image" in r.headers.get("content-type", ""):
            img_array = preprocess_image(r.content)
            prediction = model.predict(img_array)[0, :, :, 0]
            flood_pct = float(np.sum(prediction > 0.5) / (IMG_HEIGHT * IMG_WIDTH) * 100)
            return round(flood_pct, 2)
        else:
            print(f"⚠️ Failed to fetch image for ({lat},{lon}): {r.status_code}")
            return None
    except Exception as e:
        print(f"❌ Prediction error for ({lat},{lon}): {e}")
        return None