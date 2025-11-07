import os
import time
import requests
import numpy as np
from PIL import Image
from tensorflow.keras.models import load_model
from tensorflow.keras.preprocessing import image
from supabase import create_client, Client

# ==========================================================
# 🔧 CONFIGURATION
# ==========================================================
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")  # use SERVICE ROLE key in Actions
MODEL_PATH = os.getenv("MODEL_PATH", "flood_model.h5")
CHECK_INTERVAL = int(os.getenv("CHECK_INTERVAL", "600"))  # seconds between runs

# ==========================================================
# ⚙️ SETUP
# ==========================================================
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

print("Loading model...")
model = load_model(MODEL_PATH)
print("✅ Model loaded successfully!")

# ==========================================================
# 📍 FETCH LOCATIONS TO CHECK
# ==========================================================
def get_locations():
    try:
        res = supabase.table("locations").select("id,name,image_url").execute()
        return res.data or []
    except Exception as e:
        print(f"❌ Error fetching locations: {e}")
        return []

# ==========================================================
# 🌊 PREDICT FLOOD PROBABILITY
# ==========================================================
def predict_flood(image_url: str) -> float:
    try:
        img = Image.open(requests.get(image_url, stream=True).raw).resize((256, 256))
        x = image.img_to_array(img) / 255.0
        x = np.expand_dims(x, axis=0)
        prediction = model.predict(x, verbose=0)[0][0]
        return float(prediction * 100)
    except Exception as e:
        print(f"❌ Prediction failed: {e}")
        return 0.0

# ==========================================================
# ✅ FIXED: FETCH SUBSCRIBED USER EMAILS (NO CROSS-SCHEMA QUERY)
# ==========================================================
def get_user_emails_for_location(location_id: str):
    """Fetch user_ids from subscriptions, then get their emails via Auth Admin API."""
    try:
        # 1️⃣ Get user_ids subscribed to this location
        subs = supabase.table("subscriptions").select("user_id").eq("location_id", location_id).execute()
        if not subs.data:
            return []

        user_ids = [s["user_id"] for s in subs.data]

        # 2️⃣ Fetch emails for each user_id
        emails = []
        for uid in user_ids:
            try:
                user_info = supabase.auth.admin.get_user_by_id(uid)
                if user_info.user and user_info.user.email:
                    emails.append(user_info.user.email)
            except Exception as e:
                print(f"⚠️ Could not fetch email for {uid}: {e}")

        return emails

    except Exception as e:
        print(f"❌ Error fetching user emails: {e}")
        return []

# ==========================================================
# 📬 SEND ALERT
# ==========================================================
def send_alarm(location_name: str, probability: float, emails: list[str]):
    if not emails:
        print("...but no users are subscribed to this location.")
        return

    message = f"🚨 Flood Alert: {location_name} — {probability:.2f}% confidence."
    print(f"Sending alert to {len(emails)} users: {emails}")
    # TODO: integrate your notification service (email/SMS/push)

# ==========================================================
# 🔁 MAIN LOOP
# ==========================================================
def main_loop():
    print("--- Worker starting main loop ---")

    locations = get_locations()
    if not locations:
        print("No locations found.")
        return

    print(f"Fetching locations to check...")

    for loc in locations:
        loc_id = loc["id"]
        loc_name = loc["name"]
        img_url = loc["image_url"]

        print(f"Checking location: {loc_name} ({loc_id})")
        prob = predict_flood(img_url)
        print(f"✅ Prediction complete: {prob:.2f}%")

        if prob > 80.0:
            print(f"🔥 ALARM TRIGGERED! ({prob:.2f}%)")
            emails = get_user_emails_for_location(loc_id)
            send_alarm(loc_name, prob, emails)
        else:
            print(f"🌤 Safe ({prob:.2f}%)")

    print("--- Worker loop finished ---")

# ==========================================================
# 🚀 ENTRY POINT
# ==========================================================
if __name__ == "__main__":
    while True:
        main_loop()
        time.sleep(CHECK_INTERVAL)
