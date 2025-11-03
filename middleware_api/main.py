import os
from fastapi import FastAPI, Depends, HTTPException, Header
from supabase import create_client, Client
from pydantic import BaseModel
from dotenv import load_dotenv
from fastapi.middleware.cors import CORSMiddleware  # <-- IMPORTED
from typing import Annotated                   # <-- IMPORTED

# Load environment variables
load_dotenv()

# Supabase setup
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

app = FastAPI(title="Flood Alarm - Middleware API")

# --- ADD CORS MIDDLEWARE ---
# This block allows your frontend to talk to this backend
origins = [
    "https://ashudev05.github.io",  # Your deployed GitHub Pages frontend
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],  # Allows GET, POST, DELETE, etc.
    allow_headers=["*"],  # Allows all headers, including "user-id"
)
# --- END CORS MIDDLEWARE ---


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

# --- Auth Dependency (Simple Header) ---
# This is a cleaner way to write the dependency
async def get_user_id(user_id: Annotated[str, Header(alias="user-id")]):
    if not user_id:
        raise HTTPException(status_code=401, detail="User-ID header missing")
    return user_id

# --- API Endpoints ---
@app.get("/")
def root():
    return {"message": "Flood Alarm Middleware API"}

@app.post("/subscribe", status_code=201)
def subscribe_to_location(loc: LocationBase, user_id: str = Depends(get_user_id)):
    try:
        # 1. Find or create the location.
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

