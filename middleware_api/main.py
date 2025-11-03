import os
from fastapi import FastAPI, Depends, HTTPException, Header, Query
from fastapi.middleware.cors import CORSMiddleware
from supabase import create_client, Client
from pydantic import BaseModel
from dotenv import load_dotenv
from typing import Annotated, Any

# --- New Imports for Prediction ---
import numpy as np
import tensorflow as tf
from prediction_utils import load_prediction_model, get_prediction

# Load environment variables
load_dotenv()

# --- Load Model on Startup ---
# This will run when the Render service boots up
print("Loading ML model...")
model = load_prediction_model()
print("ML model loaded successfully.")


# Supabase setup
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

app = FastAPI(title="Flood Alarm - Middleware API")

# --- CORS Middleware ---
# Define the list of allowed origins
origins = [
    "http://localhost:5173",
    "http://localhost:5174",
    "https://ashudev05.github.io", # Your deployed frontend
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"], # Allows all methods
    allow_headers=["*"], # Allows all headers
)

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

# --- Auth Dependency ---
async def get_user_id(user_id: Annotated[str | None, Header()] = None):
    if not user_id:
        raise HTTPException(status_code=401, detail="User-ID header missing")
    return user_id

# --- API Endpoints ---

@app.get("/")
def root():
    return {"message": "Flood Alarm Middleware API"}

# --- NEW PREDICTION ENDPOINT ---
@app.get("/predict")
def predict_on_demand(
    lat: float = Query(...), 
    lon: float = Query(...),
    user_id: str = Depends(get_user_id) # Protects the endpoint
):
    """
    Runs an on-demand prediction for a specific lat/lon.
    """
    try:
        print(f"Running on-demand prediction for ({lat}, {lon})")
        # Use the get_prediction function from prediction_utils
        flood_pct = get_prediction(model, lat, lon)

        if flood_pct is None:
            raise HTTPException(status_code=500, detail="Failed to fetch or process satellite image")
            
        return {
            "latitude": lat,
            "longitude": lon,
            "flood_percentage": flood_pct
        }

    except Exception as e:
        print(f"Error during prediction: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# --- bestehende Subscription Endpoints ---

@app.post("/subscribe", status_code=201)
def subscribe_to_location(loc: LocationBase, user_id: str = Depends(get_user_id)):
    try:
        location_data = supabase.table("locations").upsert(
            {"lat": loc.lat, "lon": loc.lon, "name": loc.name}
        ).execute()

        location_id = location_data.data[0]['id']

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

