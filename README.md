# KhataSync 🛒💳

**Credit scoring for the invisible economy.** A remote Kirana store cash flow underwriting engine.

## 🚀 The Concept

Traditional lenders require heavy paperwork, ITRs, and digital transaction histories—documentation that tier-2 and tier-3 Kirana stores often lack. KhataSync eliminates the need for physical field visits and paperwork by providing a 15-minute, highly secure credit assessment right from the shopkeeper's phone.

Instead of financial history, we underwrite based on real-time **operational reality** using a proprietary 4-signal Fusion Model:

1. **📸 Visual Intelligence:** Analyzes shelf density, SKU diversity, and inventory value via computer vision.
2. **📍 Geo Intelligence:** Evaluates footfall potential and competitor density using location APIs.
3. **🔀 ShopLive Protocol:** An anti-fraud challenge that forces chronological, GPS-stamped photo capture of specific shop zones to prevent staged inventory.
4. **🧠 Operational Knowledge:** A timed cognitive test proving the user is the actual operator by testing active knowledge of inventory locations and pricing.

---

## 🛠️ Project Structure

KhataSync is built as a unified monolith for seamless mobile demoing:
- **Backend:** FastAPI (Python) routing the ML models and underwriting logic.
- **Frontend:** Vanilla JS + CSS mobile app served directly from the backend's `/static` directory.

---

## ⚙️ Local Setup

1. **Clone the repository:**
   ```bash
   git clone [https://github.com/Ishankalhe911/tensorX.git](https://github.com/Ishankalhe911/tensorX.git)
   cd tensorX

```
 2. **Set up the virtual environment (Windows):**
   ```bash
   python -m venv venv
   .\venv\Scripts\activate
   
   ```
 3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   
   ```
 4. **Environment Variables:**
   Create a .env file in the root directory.
   ```env
   GOOGLE_MAPS_API_KEY=your_api_key_here
   
   ```
   *(Note: The app has safe fallbacks and will run locally even without the API key).*
## 🎬 How to Execute the Live Mobile Demo (Hackathon Workflow)
To show the app running live on your phone to the judges, follow this strict sequence:
 1. **Start the FastAPI Server:**
   Ensure your terminal is in the project root and run:
   ```bash
   python main.py
   
   ```
   *The server will start on http://localhost:8000 and will automatically serve the UI from the static/index.html file.*
 2. **Start the Ngrok Tunnel:**
   Open a **second** terminal window and run:
   ```bash
   ngrok http 8000
   
   ```
 3. **Demo on Mobile:**
   * Copy the generated Forwarding URL from the ngrok terminal (e.g., https://xxxx-xx-xx.ngrok-free.app).
   * Open that URL on your smartphone's browser.
   * Complete the ShopLive assessment live. The frontend will communicate seamlessly with your local Python backend!
## 📡 API Reference
| Method | Route | Description |
|---|---|---|
| GET | / | Serves the frontend mobile UI |
| GET | /health | Liveness check for all 4 intelligence modules |
| GET | /api/challenge | Generates a randomized ShopLive zone challenge |
| POST | /api/analyze | Main underwriting pipeline. Accepts multipart form data, runs fusion model, returns JSON report. |
| POST | /api/analyze/demo | Offline fallback endpoint returning pre-computed pass/verify/fail scenarios. |
### Full Analysis Payload (POST /api/analyze)
The frontend sends data to this endpoint via multipart/form-data. All fields have safe backend defaults to prevent 422 Unprocessable Entity crashes during spotty mobile connections.
```text
images:               [File Array]
lat:                  18.5204
lng:                  73.8567
employee_count:       1
photo_metadata_json:  [{"lat":18.5204,"lng":73.8567,"timestamp":1700000000,"zone_id":"left_shelf"}]
audio_transcript:     "The atta is on the left shelf, it costs 280 rupees"
video_duration:       8.5

```
### Demo Mode Endpoints (For UI testing without live ML)
```http
POST /api/analyze/demo?scenario=pass
POST /api/analyze/demo?scenario=verify
POST /api/analyze/demo?scenario=fail




