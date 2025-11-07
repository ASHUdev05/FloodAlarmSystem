import os
import time
from datetime import datetime, timedelta, timezone
from dotenv import load_dotenv
from supabase import create_client, Client
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail
from prediction_utils import load_prediction_model, get_prediction

# ==========================================================
# 🔧 CONFIGURATION
# ==========================================================
load_dotenv()

THRESHOLD_PERCENT = 85.0
CHECK_INTERVAL_HOURS = 1
SLEEP_BETWEEN_RUNS = int(os.getenv("CHECK_INTERVAL", "3600"))

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")  # Service role key
SENDGRID_API_KEY = os.getenv("SENDGRID_API_KEY")
FROM_EMAIL = os.getenv("FROM_EMAIL")

# ==========================================================
# ⚙️ SETUP
# ==========================================================
print("Loading model (via prediction_utils.py)...")

os.environ["CUDA_VISIBLE_DEVICES"] = "-1"
os.environ["TF_CPP_MIN_LOG_LEVEL"] = "2"

model = load_prediction_model()
print("✅ Model loaded successfully!\n")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# ==========================================================
# 📍 FETCH LOCATIONS TO CHECK
# ==========================================================
def get_locations_to_check():
    """Get all unique locations not checked recently."""
    print("Fetching locations to check...")
    query_time = (datetime.now(timezone.utc) - timedelta(hours=CHECK_INTERVAL_HOURS)).isoformat()

    try:
        response = supabase.table("locations").select("*").or_(
            f"last_checked_at.lt.{query_time},last_checked_at.is.null"
        ).execute()
        return response.data or []
    except Exception as e:
        print(f"❌ Error fetching locations: {e}")
        return []


def update_location_timestamp(location_id):
    try:
        supabase.table("locations").update({
            "last_checked_at": datetime.now(timezone.utc).isoformat()
        }).eq("id", location_id).execute()
    except Exception as e:
        print(f"❌ Error updating timestamp: {e}")


# ==========================================================
# 👥 USERS, EMAILS & NOTIFICATIONS
# ==========================================================
def get_subscribed_users(location_id):
    """Get all subscribed users for a location."""
    try:
        subs_response = supabase.table("subscriptions") \
            .select("user_id") \
            .eq("location_id", location_id) \
            .execute()

        if not subs_response.data:
            print("...no users subscribed.")
            return []

        user_ids = [sub["user_id"] for sub in subs_response.data]

        users = []
        for uid in user_ids:
            # Supabase admin API fetch
            user_resp = supabase.auth.admin.get_user_by_id(uid)
            if user_resp and user_resp.user and user_resp.user.email:
                users.append({
                    "id": uid,
                    "email": user_resp.user.email
                })

        return users

    except Exception as e:
        print(f"❌ Error fetching user emails: {e}")
        return []


def send_alert_email(user_email, location_name, flood_pct):
    """Send alert email using SendGrid."""
    print(f"Sending alert to {user_email} for {location_name}...")
    message = Mail(
        from_email=FROM_EMAIL,
        to_emails=user_email,
        subject=f"🚨 FLOOD ALERT: {flood_pct:.1f}% risk at {location_name}",
        html_content=f"""
        <strong>Warning!</strong><br>
        <p>Detected flood risk of <b>{flood_pct:.1f}%</b> at your subscribed location <b>{location_name}</b>.</p>
        <p>Please take necessary precautions.</p>
        """
    )
    try:
        sg = SendGridAPIClient(SENDGRID_API_KEY)
        sg.send(message)
    except Exception as e:
        print(f"❌ Error sending email: {e}")


def create_notification(user_id, location_id, location_name, flood_pct):
    """Record notification to Supabase."""
    try:
        print(f"Registering notification for user {user_id}...")
        supabase.table("notifications").insert({
            "user_id": user_id,
            "location_id": location_id,
            "location_name": location_name,
            "flood_percentage": flood_pct,
            "is_read": False
        }).execute()
    except Exception as e:
        print(f"❌ Error creating notification: {e}")


# ==========================================================
# 🔁 MAIN LOOP
# ==========================================================
def main_loop():
    print("--- Worker starting main loop ---")
    locations = get_locations_to_check()
    if not locations:
        print("No locations to check.")
        return

    for loc in locations:
        print(f"\n→ Checking location: {loc['name']} ({loc['id']})")
        try:
            flood_pct = get_prediction(model, loc["lat"], loc["lon"])
        except Exception as e:
            print(f"❌ Prediction error: {e}")
            continue

        update_location_timestamp(loc["id"])
        if flood_pct is None:
            print("⚠️ Skipping due to failed prediction.")
            continue

        print(f"✅ Prediction complete: {flood_pct:.2f}%")

        if flood_pct > THRESHOLD_PERCENT:
            print(f"🔥 ALARM TRIGGERED! ({flood_pct:.2f}%)")
            users = get_subscribed_users(loc["id"])

            if not users:
                print("...but no users subscribed.")
                continue

            for u in users:
                send_alert_email(u["email"], loc["name"], flood_pct)
                create_notification(u["id"], loc["id"], loc["name"], flood_pct)
        else:
            print(f"🌤 Safe ({flood_pct:.2f}%)")

        print("-" * 40)

    print("--- Worker loop finished ---\n")


# ==========================================================
# 🚀 ENTRY POINT
# ==========================================================
if __name__ == "__main__":
    while True:
        main_loop()
        print(f"Sleeping for {SLEEP_BETWEEN_RUNS} seconds...\n")
        time.sleep(SLEEP_BETWEEN_RUNS)
