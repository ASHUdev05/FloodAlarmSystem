import os
from fastapi import FastAPI, Depends, HTTPException, Header
from typing import Annotated
from fastapi.middleware.cors import CORSMiddleware
from supabase import create_client, Client
from pydantic import BaseModel
from dotenv import load_dotenv
import uvicorn
from contextlib import asynccontextmanager
from typing import Optional

# Import the prediction utils
from prediction_utils import load_prediction_model, get_prediction

# Load environment variables
load_dotenv()

# --- App State ---
# Use a dictionary to store objects that are available during the app's lifespan
app_state = {}

@asynccontextmanager
async def lifespan(app: FastAPI):
    # --- Startup ---
    print("Loading ML model...")
    # Load the model on startup and store it in app_state
    app_state["model"] = load_prediction_model()
    if app_state["model"] is None:
        print("CRITICAL: ML Model failed to load. /predict endpoint will not work.")
    else:
        print("ML model loaded successfully.")
    
    yield
    
    # --- Shutdown ---
    print("Clearing app state...")
    app_state.clear()

# --- FastAPI App Initialization ---
app = FastAPI(title="Flood Alarm - Middleware API", lifespan=lifespan)

# --- CORS Middleware ---
origins = [
    "http://localhost:5173",
    "http://localhost:5174",
    "https://ashudev05.github.io",
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Supabase Setup ---
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)


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
async def get_user_id(user_id: Annotated[str, Header()] = None):
    if not user_id:
        raise HTTPException(status_code=401, detail="User-ID header missing")
    return user_id

# --- API Endpoints ---
@app.get("/")
def root():
    return {"message": "Flood Alarm Middleware API", "model_loaded": app_state.get("model") is not None}

@app.get("/predict")
async def predict_live(lat: float, lon: float, user_id: Annotated[str, Depends(get_user_id)]):
    print(f"Running on-demand prediction for ({lat}, {lon})")
    
    model = app_state.get("model")
    if model is None:
        raise HTTPException(status_code=500, detail="ML model is not loaded on server.")

    prediction_pct = get_prediction(model, lat, lon)

    if prediction_pct is None:
        raise HTTPException(status_code=503, detail="Satellite data not available for this location or date.")
        
    return {"latitude": lat, "longitude": lon, "flood_percentage": prediction_pct}

# --- Subscription Endpoints ---

@app.post("/subscribe", status_code=201)
async def subscribe_to_location(loc: LocationBase, user_id: Annotated[str, Depends(get_user_id)]):
    try:
        location_id = None
        
        # 1. Check if location already exists
        # We must round the lat/lon to prevent tiny floating-point duplicates
        # Rounding to 6 decimal places is accurate to ~11cm
        rounded_lat = round(loc.lat, 6)
        rounded_lon = round(loc.lon, 6)

        location_res = supabase.table("locations").select("id").eq("lat", rounded_lat).eq("lon", rounded_lon).execute()
        
        if location_res.data:
            # Location exists, use its ID
            location_id = location_res.data[0]['id']
        else:
            # Location does not exist, create it
            new_loc_res = supabase.table("locations").insert({
                "lat": rounded_lat,
                "lon": rounded_lon,
                "name": loc.name
            }).select("id").execute()
            
            if not new_loc_res.data:
                 raise Exception("Failed to create new location entry.")
            location_id = new_loc_res.data[0]['id']

        # 2. Now, try to create the subscription
        subscription_data = supabase.table("subscriptions").insert({
            "user_id": user_id,
            "location_id": location_id
        }).select("id").execute()

        return {"status": "success", "subscription_id": subscription_data.data[0]['id']}

    except Exception as e:
        error_str = str(e)
        # Check for the *subscription* constraint violation (user is already subscribed)
        if "user_location_unique" in error_str:
            raise HTTPException(status_code=400, detail="You are already subscribed to this location.")
        
        # Check for the *location* constraint violation (this is a fallback)
        if "unique_lat_lon" in error_str:
            raise HTTPException(status_code=400, detail="A location with these coordinates already exists, but subscription failed.")

        # Log the unexpected error and return a 500
        print(f"Error in /subscribe: {e}")
        raise HTTPException(status_code=500, detail="An internal server error occurred.")


@app.get("/subscriptions", response_model=list[Subscription])
async def get_my_subscriptions(user_id: Annotated[str, Depends(get_user_id)]):
    try:
        data = supabase.rpc("get_user_subscriptions", {"p_user_id": user_id}).execute()
        return data.data
    except Exception as e:
        print(f"Error in /subscriptions: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/subscribe/{location_id}")
async def unsubscribe(location_id: str, user_id: Annotated[str, Depends(get_user_id)]):
    try:
        supabase.table("subscriptions").delete().match({
            "user_id": user_id,
            "location_id": location_id
        }).execute()
        return {"status": "success", "message": "Unsubscribed"}
    except Exception as e:
        print(f"Error in /unsubscribe: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Main entry point (for local running)
if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)