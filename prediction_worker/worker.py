import os
import time
from datetime import datetime, timedelta, timezone
from dotenv import load_dotenv
from supabase import create_client, Client
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail
from prediction_utils import load_prediction_model, get_prediction

# --- Config ---
load_dotenv()
THRESHOLD_PERCENT = 85.0
CHECK_INTERVAL_HOURS = 1
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY") # Service role key
SENDGRID_API_KEY = os.environ.get("SENDGRID_API_KEY")
FROM_EMAIL = os.environ.get("FROM_EMAIL")

# --- Initialize Clients ---
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
model = load_prediction_model()

def get_locations_to_check():
    """Get all unique locations that haven't been checked in the last N hours."""
    print("Fetching locations to check...")
    query_time = (datetime.now(timezone.utc) - timedelta(hours=CHECK_INTERVAL_HOURS)).isoformat()
    
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
            {"last_checked_at": datetime.now(timezone.utc).isoformat()}
        ).eq("id", location_id).execute()
    except Exception as e:
        print(f"❌ Error updating timestamp: {e}")

# --- MODIFICATION 1: Get user ID and email ---
def get_subscribed_users(location_id):
    """Get all users (id and email) subscribed to a specific location."""
    try:
        # We join subscriptions with auth.users to get both ID and email
        response = supabase.table("subscriptions").select(
            "user_id, users:auth.users ( email )"
        ).eq("location_id", location_id).execute()
        
        if response.data:
            # Re-format the data to be a simple list of dicts
            return [
                {"id": user["user_id"], "email": user["users"]["email"]} 
                for user in response.data 
                if user.get("users") # Ensure the join was successful
            ]
        return []
    except Exception as e:
        print(f"❌ Error fetching user emails/ids: {e}")
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
        # We catch the error, log it, but do NOT stop the worker
        print(f"❌ Error sending email: {e}")

# --- MODIFICATION 2: Function to create the notification ---
def create_notification(user_id, location_id, location_name, flood_pct):
    """Writes the alarm to the new 'notifications' table."""
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


def main_loop():
    print("--- Worker starting main loop ---")
    locations = get_locations_to_check()
    if not locations:
        print("No locations to check. Sleeping.")
        return

    for loc in locations:
        print(f"\nChecking location: {loc['name']} ({loc['id']})")
        
        flood_pct = get_prediction(model, loc['lat'], loc['lon'])
        update_location_timestamp(loc['id'])

        if flood_pct is None:
            continue

        print(f"✅ Prediction complete: {flood_pct}%")

        if flood_pct > THRESHOLD_PERCENT:
            print(f"🔥 ALARM TRIGGERED! ({flood_pct}%)")
            users_to_alert = get_subscribed_users(loc['id'])
            
            if not users_to_alert:
                print("...but no users are subscribed to this location.")
                continue

            # --- MODIFICATION 3: Loop over user objects, not just emails ---
            for user in users_to_alert:
                # 1. Send email (will try and continue on error)
                send_alert_email(user['email'], loc['name'], flood_pct)
                
                # 2. Create notification (the reliable fallback)
                create_notification(user['id'], loc['id'], loc['name'], flood_pct)
        
        time.sleep(2)

    print("\n--- Worker loop finished ---")


if __name__ == "__main__":
    main_loop()