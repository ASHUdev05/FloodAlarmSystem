import os
from fastapi import FastAPI, Depends, HTTPException, Header
from supabase import create_client, Client
from pydantic import BaseModel
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Supabase setup
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

app = FastAPI(title="Flood Alarm - Middleware API")

# --- Pydantic Models ---
class LocationBase(BaseModel):
    lat: float
    lon: float
    name: str

class Subscription(BaseModel):
    location_id: str
    name: str
    lat: float
    lon: float

# --- Auth Dependency (Placeholder) ---
# In a real React app, your user would log in (using Supabase Auth)
# and send an "Authorization: Bearer <JWT_TOKEN>" header.
# This function would verify the token and return the user's ID.
# For this demo, we'll just require a "user-id" header.
async def get_user_id(user_id: str = Header(...)):
    if not user_id:
        raise HTTPException(status_code=401, detail="User-ID header missing")
    # In a real app, you'd validate this user_id or token
    return user_id

# --- API Endpoints ---
@app.get("/")
def root():
    return {"message": "Flood Alarm Middleware API"}

@app.post("/subscribe", status_code=201)
def subscribe_to_location(loc: LocationBase, user_id: str = Depends(get_user_id)):
    try:
        # 1. Find or create the location. `upsert` is perfect here.
        # It finds a row with matching lat/lon or inserts a new one.
        location_data = supabase.table("locations").upsert(
            {"lat": loc.lat, "lon": loc.lon, "name": loc.name}
        ).execute()

        location_id = location_data.data[0]['id']

        # 2. Create the subscription linking the user to the location
        subscription_data = supabase.table("subscriptions").insert({
            "user_id": user_id,
            "location_id": location_id
        }).execute()

        return {"status": "success", "subscription_id": subscription_data.data[0]['id']}

    except Exception as e:
        if "user_location_unique" in str(e):
            raise HTTPException(status_code=400, detail="Already subscribed to this location")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/subscriptions", response_model=list[Subscription])
def get_my_subscriptions(user_id: str = Depends(get_user_id)):
    # This query joins subscriptions with locations to get all info
    try:
        # Use rpc (Remote Procedure Call) for a custom SQL join
        data = supabase.rpc("get_user_subscriptions", {"p_user_id": user_id}).execute()
        return data.data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/subscribe/{location_id}")
def unsubscribe(location_id: str, user_id: str = Depends(get_user_id)):
    try:
        supabase.table("subscriptions").delete().match({
            "user_id": user_id,
            "location_id": location_id
        }).execute()
        return {"status": "success", "message": "Unsubscribed"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))