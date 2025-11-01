# 🌊 Flood Alarm System (FastAPI + Deep Learning)

A real-time flood detection API using **U-Net (TensorFlow/Keras)** and **FastAPI**.  
It predicts floods from uploaded satellite images or live NASA GIBS data.

---

## 🚀 Features
- 🧠 **AI Model**: U-Net for flood segmentation  
- 📸 **Image Upload**: Detect floods from satellite photos  
- 🌍 **Live Monitoring**: Location-based, real-time updates  
- ⚡ **FastAPI Backend** with Swagger UI  
- 🔗 **Ngrok Integration** for Colab sharing  
- 🧭 **Dynamic Location Change** via `/set_location`

---

## 🧠 Tech Stack
FastAPI • Uvicorn • TensorFlow/Keras • Pillow • NumPy • NASA GIBS • Ngrok

---

## 📁 Project Files
📦 FloodAlarmSystem
├── main.py # FastAPI backend
├── flood_model.h5 # Trained model
├── requirements.txt # Dependencies
├── flood_alarm.ipynb # Colab notebook
└── README.md # Docs

## ⚙️ Quick Setup

### 🧭 Google Colab (Recommended)
```bash
!git clone https://github.com/<your-username>/FloodAlarmSystem.git
%cd FloodAlarmSystem
!pip install -r requirements.txt
python
Copy code
from pyngrok import ngrok
ngrok.set_auth_token("YOUR_NGROK_AUTH_TOKEN")
public_url = ngrok.connect(8000)
print(public_url)
!uvicorn main:app --host 0.0.0.0 --port 8000

Access API:

Docs → <ngrok-url>/docs
Live Feed → <ngrok-url>/live

### Run Locally:
git clone https://github.com/<your-username>/FloodAlarmSystem.git
cd FloodAlarmSystem
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload

Open → http://localhost:8000/docs

| Endpoint                            | Method | Description                       |
| ----------------------------------- | ------ | --------------------------------- |
| `/`                                 | GET    | Health check                      |
| `/predict`                          | POST   | Predict flood from uploaded image |
| `/live`                             | GET    | Get live flood data               |
| `/set_location?lat=19.07&lon=72.87` | GET    | Set live location                 |
| `/docs`                             | GET    | API docs (Swagger UI)             |

⚙️ Config

Default: Sunderbans Region (LATITUDE = 21.9497, LONGITUDE = 89.1833)
Change dynamically via /set_location.
