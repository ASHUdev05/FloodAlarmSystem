import os
import time
from datetime import datetime, timedelta, timezone  # <-- FIX 1
from dotenv import load_dotenv
from supabase import create_client, Client
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail
from prediction_utils import load_prediction_model, get_prediction

# --- Config ---
load_dotenv()
THRESHOLD_PERCENT = 85.0  # Trigger alert at 85%
CHECK_INTERVAL_HOURS = 1  # How often to check each location
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")  # Service role key
SENDGRID_API_KEY = os.environ.get("SENDGRID_API_KEY")
FROM_EMAIL = os.environ.get("FROM_EMAIL")

# --- Initialize Clients ---
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
model = load_prediction_model()

def get_locations_to_check():
    """Get all unique locations that haven't been checked in the last N hours."""
    print("Fetching locations to check...")
    # 'lt' means 'less than'. Find locations checked > 1 hour ago
    query_time = (datetime.now(timezone.utc) - timedelta(hours=CHECK_INTERVAL_HOURS)).isoformat() # <-- FIX 2
    
    try:
        response = supabase.table("locations").select("*").or_(
            f"last_checked_at.lt.{query_time},last_checked_at.is.null"
        ).execute()
        return response.data
    except Exception as e:
        print(f"❌ Error fetching locations: {e}")
        return []

def update_location_timestamp(location_id):
    """Update the 'last_checked_at' field for a location."""
    try:
        supabase.table("locations").update(
            {"last_checked_at": datetime.now(timezone.utc).isoformat()}  # <-- FIX 3
        ).eq("id", location_id).execute()
    except Exception as e:
        print(f"❌ Error updating timestamp: {e}")

def get_subscribed_users(location_id):
    """Get all users subscribed to a specific location."""
    try:
        # We need the user's email, which is in the 'auth.users' table
        response = supabase.rpc("get_emails_for_location", {
            "p_location_id": location_id
        }).execute()
        
        if response.data:
            return [user['email'] for user in response.data]
        return []
    except Exception as e:
        print(f"❌ Error fetching user emails: {e}")
        return []

def send_alert_email(user_email, location_name, flood_pct):
    """Use SendGrid to send a single email."""
    print(f"Sending alert to {user_email} for {location_name}...")
    message = Mail(
        from_email=FROM_EMAIL,
        to_emails=user_email,
        subject=f"🚨 FLOOD ALARM: High Risk ({flood_pct}%) at {location_name}",
        html_content=f"""
        <strong>Warning!</strong><br>
        <p>Our system has detected a high flood risk of <strong>{flood_pct}%</strong>
        at your subscribed location: <strong>{location_name}</strong>.</p>
        <p>Please take necessary precautions.</p>
        """
    )
    try:
        sg = SendGridAPIClient(SENDGRID_API_KEY)
        sg.send(message)
    except Exception as e:
        print(f"❌ Error sending email: {e}")

def main_loop():
    print("--- Worker starting main loop ---")
    locations = get_locations_to_check()
    if not locations:
        print("No locations to check. Sleeping.")
        return

    for loc in locations:
        print(f"\nChecking location: {loc['name']} ({loc['id']})")
        
        # 1. Run the prediction
        flood_pct = get_prediction(model, loc['lat'], loc['lon'])
        
        # 2. Update its timestamp so we don't check it again right away
        update_location_timestamp(loc['id'])

        if flood_pct is None:
            continue

        print(f"✅ Prediction complete: {flood_pct}%")

        # 3. Check against threshold
        if flood_pct > THRESHOLD_PERCENT:
            print(f"🔥 ALARM TRIGGERED! ({flood_pct}%)")
            users_to_alert = get_subscribed_users(loc['id'])
            
            if not users_to_alert:
                print("...but no users are subscribed to this location.")
                continue

            for email in users_to_alert:
                send_alert_email(email, loc['name'], flood_pct)
        
        time.sleep(2) # Avoid rate-limiting

    print("\n--- Worker loop finished ---")


if __name__ == "__main__":
    main_loop()