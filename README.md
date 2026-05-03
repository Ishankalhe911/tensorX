# KhataSync Backend

Remote kirana store cash flow underwriting engine.

## Setup

```bash
pip install -r requirements.txt
cp .env.example .env
# Add your GOOGLE_MAPS_API_KEY to .env
uvicorn main:app --reload --port 8000
```

## API Endpoints

| Method | Route | Description |
|--------|-------|-------------|
| GET | `/health` | Check all modules are running |
| GET | `/api/challenge` | Generate a new ShopLive challenge |
| POST | `/api/analyze/images` | Full analysis with real images |
| POST | `/api/analyze/demo?scenario=pass` | Demo mode (pass/verify/fail) |

## Demo Mode (no API keys needed)
```
POST /api/analyze/demo?scenario=pass
POST /api/analyze/demo?scenario=verify
POST /api/analyze/demo?scenario=fail
```

## Full Analysis
```
POST /api/analyze/images
Content-Type: multipart/form-data

images:               [files]
lat:                  18.5204
lng:                  73.8567
employee_count:       1
photo_metadata_json:  [{"lat":18.5204,"lng":73.8567,"timestamp":1700000000,"zone_id":"left_shelf"}]
audio_transcript:     "The atta is on the left shelf, it costs 280 rupees"
video_duration:       8.5
```