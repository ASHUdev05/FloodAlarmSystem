import os
import time
from supabase import create_client, Client
from prediction_utils import load_prediction_model, get_prediction

# ==========================================================
# 🔧 CONFIGURATION
# ==========================================================
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")  # use SERVICE ROLE key in Actions
CHECK_INTERVAL = int(os.getenv("CHECK_INTERVAL", "600"))  # seconds between runs

# ==========================================================
# ⚙️ SETUP
# ==========================================================
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

print("Loading model (via prediction_utils.py)...")
model = load_prediction_model()  # ✅ uses dynamic path and custom losses
print("✅ Model loaded successfully!\n")

# ==========================================================
# 📍 FETCH LOCATIONS TO CHECK
# ==========================================================
def get_locations():
    try:
        res = supabase.table("locations").select("id, name, latitude, longitude").execute()
        return res.data or []
    except Exception as e:
        print(f"❌ Error fetching locations: {e}")
        return []

# ==========================================================
# ✅ FETCH SUBSCRIBED USER EMAILS (CLEANED)
# ==========================================================
def get_user_emails_for_location(location_id: str):
    """Fetch user_ids from subscriptions, then get their emails via Auth Admin API."""
    try:
        subs = supabase.table("subscriptions").select("user_id").eq("location_id", location_id).execute()
        if not subs.data:
            return []

        user_ids = [s["user_id"] for s in subs.data]
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

    message = f"🚨 Flood Alert: {location_name} — {probability:.2f}% flood risk detected!"
    print(f"Sending alert to {len(emails)} users: {emails}")
    # TODO: integrate your notification service (email/SMS/push)
    # Example placeholder:
    # send_email(emails, subject="Flood Alert", body=message)

# ==========================================================
# 🔁 MAIN LOOP
# ==========================================================
def main_loop():
    print("--- Worker starting main loop ---")

    locations = get_locations()
    if not locations:
        print("No locations found.")
        return

    print(f"Fetched {len(locations)} locations to check...\n")

    for loc in locations:
        loc_id = loc["id"]
        loc_name = loc["name"]
        lat, lon = loc["latitude"], loc["longitude"]

        print(f"Checking location: {loc_name} ({lat}, {lon})")
        prob = get_prediction(model, lat, lon)

        if prob is None:
            print(f"⚠️ Skipped {loc_name} due to prediction error.\n")
            continue

        print(f"✅ Prediction complete: {prob:.2f}%")

        if prob > 80.0:
            print(f"🔥 ALARM TRIGGERED! ({prob:.2f}%)")
            emails = get_user_emails_for_location(loc_id)
            send_alarm(loc_name, prob, emails)
        else:
            print(f"🌤 Safe ({prob:.2f}%)")

        print("-" * 40)

    print("--- Worker loop finished ---\n")

# ==========================================================
# 🚀 ENTRY POINT
# ==========================================================
def main_loop():
    print("--- Worker starting main loop ---")

    try:
        print("Fetching locations from Supabase...")
        locations = get_locations()
        print(f"Fetched {len(locations)} locations.")
    except Exception as e:
        print(f"❌ Error while fetching locations: {e}")
        return

    if not locations:
        print("No locations found.")
        return

    for loc in locations:
        loc_id = loc["id"]
        loc_name = loc["name"]
        lat, lon = loc["latitude"], loc["longitude"]

        print(f"→ Checking location: {loc_name} ({lat}, {lon})")

        try:
            prob = get_prediction(model, lat, lon)
            print(f"✅ Prediction result: {prob}")
        except Exception as e:
            print(f"❌ Prediction error for {loc_name}: {e}")
            continue

        if prob is None:
            print(f"⚠️ Skipped {loc_name} due to prediction failure.")
            continue

        if prob > 80.0:
            print(f"🔥 Flood alert triggered for {loc_name}!")
            emails = get_user_emails_for_location(loc_id)
            send_alarm(loc_name, prob, emails)
        else:
            print(f"🌤 Safe ({prob:.2f}%)")

        print("-" * 40)

    print("--- Worker loop finished ---\n")

if __name__ == "__main__":
    while True:
        main_loop()
        print(f"Sleeping for {CHECK_INTERVAL} seconds...\n")
        time.sleep(CHECK_INTERVAL)
