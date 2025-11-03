import os
from fastapi import FastAPI, Depends, HTTPException, Header, Annotated
from fastapi.middleware.cors import CORSMiddleware
from supabase import create_client, Client
from pydantic import BaseModel
from dotenv import load_dotenv
import uvicorn
from contextlib import asynccontextmanager

# Import the new prediction utils
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

# --- NEW: /predict Endpoint ---
@app.get("/predict")
def predict_live(lat: float, lon: float, user_id: Annotated[str, Depends(get_user_id)]):
    print(f"Running on-demand prediction for ({lat}, {lon})")
    
    model = app_state.get("model")
    if model is None:
        raise HTTPException(status_code=500, detail="ML model is not loaded on server.")

    # Get_prediction now returns None on "No Data"
    prediction_pct = get_prediction(model, lat, lon)

    # --- FIX: Handle "No Data" (None) case ---
    if prediction_pct is None:
        raise HTTPException(status_code=503, detail="Satellite data not available for this location or date.")
    # --- END FIX ---
        
    return {"latitude": lat, "longitude": lon, "flood_percentage": prediction_pct}

# --- Subscription Endpoints ---
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
        print(f"Error in /subscribe: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/subscriptions", response_model=list[Subscription])
def get_my_subscriptions(user_id: str = Depends(get_user_id)):
    try:
        data = supabase.rpc("get_user_subscriptions", {"p_user_id": user_id}).execute()
        return data.data
    except Exception as e:
        print(f"Error in /subscriptions: {e}")
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
        print(f"Error in /unsubscribe: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Main entry point (for local running)
if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)