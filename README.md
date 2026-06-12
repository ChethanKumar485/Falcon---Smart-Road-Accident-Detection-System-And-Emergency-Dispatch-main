# 🦅 FALCON — Smart Road Accident Detection System v2.0

**Fatality Alert & Crash Locator Over Networks**

A full-stack AI-powered road accident detection and emergency dispatch system with live IP webcam support, real-time hospital/police finder, WhatsApp alerts, auto-generated police reports, and a stunning tactical UI.

---

## 🚀 Features

### 🎥 Live Detection
- **IP Webcam Support** — Paste any IP webcam URL (Android "IP Webcam" app, MJPEG, RTSP)
- **AI-Powered Detection** — Computer vision (optical flow, motion analysis, edge change detection)
- **Real-time Analysis** — Processes every 5th frame for performance
- **HUD Overlay** — Tactical heads-up display with scan animation on live feed
- **Confidence Score** — Shows detection confidence % in real time

### 🏥 Hospital Finder
- Finds **real nearby hospitals** using OpenStreetMap / Overpass API
- Shows: distance, ETA, available doctors, specialties, beds, phone, emergency status
- **Doctor Availability** — Lists doctors on duty with specialty
- Auto-notifies hospitals via SMS + Email on accident detection

### 🚔 Police Finder
- Finds **real nearby police stations** using OpenStreetMap
- Shows: distance, ETA, officers on duty with badge numbers
- Auto-notifies nearest stations via SMS

### 📱 WhatsApp Integration
- Sends accident photo + location to configured numbers via **Twilio WhatsApp API**
- Also supports **Meta WhatsApp Business API**
- Message includes: location, map link, severity, nearest hospital, nearest police
- Configurable alert numbers in UI

### 📋 Police Report Generator
- Generates professional **government-style HTML report**
- Includes: Government of India letterhead + seal
- Hospital + Doctor details table
- Police station + Officer details table
- Accident scene photo
- Actions taken log
- 3 signature fields (System, Station Officer, Superintendent)
- Printable / PDF-ready

### 🗺️ Maps
- Embedded Google Maps showing accident location
- One-click map links for hospitals and police stations
- Location auto-detection via browser GPS or IP geolocation

### 📤 Notifications
- SMS via Twilio
- Email via SMTP (Gmail, etc.)
- WhatsApp via Twilio / Meta
- All notification history shown in UI

### 🎨 UI/UX
- **Tactical dark theme** with cyan/red accents
- Real-time system log
- Detection metrics bars (motion, foreground, edge, confidence)
- Accident history with thumbnails
- Sound alert on accident detection
- Animated scan overlay on video
- Responsive 3-column layout

---

## 📦 Installation

### 1. Clone & Setup
```bash
git clone <repo>
cd falcon
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Configure Environment
```bash
cp .env.example .env
# Edit .env with your credentials
```

### 3. Run
```bash
python app.py
```
Open: **http://localhost:5000**

---

## 📱 Connecting IP Webcam

### Android (Recommended)
1. Install **"IP Webcam"** app from Play Store
2. Start server in app
3. Note the IP shown (e.g., `192.168.1.100:8080`)
4. In FALCON, paste: `http://192.168.1.100:8080/video`
5. Click **CONNECT**

### Other formats
- MJPEG: `http://IP:PORT/video`
- RTSP: `rtsp://IP:PORT/stream`
- Direct webcam: `/dev/video0` (Linux) or `0` (default cam)

---

## 📱 WhatsApp Setup

### Option A: Twilio (Easier — Free Sandbox)
1. Sign up at [twilio.com](https://www.twilio.com)
2. Join the WhatsApp sandbox: send "join <word>" to +14155238886
3. Add to `.env`:
   ```
   TWILIO_ACCOUNT_SID=ACxxxxxxx
   TWILIO_AUTH_TOKEN=xxxxxxx
   TWILIO_WHATSAPP_FROM=whatsapp:+14155238886
   WHATSAPP_ALERT_NUMBERS=+91XXXXXXXXXX
   ```

### Option B: Meta WhatsApp Business API (Production)
1. Create a Meta Developer App
2. Add WhatsApp product
3. Get Phone Number ID and token
4. Add to `.env`:
   ```
   META_WHATSAPP_TOKEN=your_token
   META_PHONE_NUMBER_ID=your_phone_id
   ```

---

## 📬 SMS & Email Setup

### Twilio SMS
```
TWILIO_FROM_NUMBER=+1XXXXXXXXXX
```

### Gmail Email
1. Enable 2-factor auth on Gmail
2. Create App Password: Google Account → Security → App Passwords
3. Add to `.env`:
   ```
   SMTP_USER=your@gmail.com
   SMTP_PASS=your_app_password
   ```

---

## 🏗️ Project Structure

```
falcon/
├── app.py                    # Main Flask application
├── requirements.txt          # Python dependencies
├── .env.example             # Environment config template
├── README.md                # This file
├── templates/
│   └── index.html           # Full tactical UI
├── static/
│   ├── css/                 # Stylesheets
│   ├── js/                  # JavaScript
│   └── accidents/           # Saved accident frames
├── utils/
│   ├── accident_detector.py # CV-based detection engine
│   ├── location_service.py  # GPS/IP geolocation
│   ├── hospital_finder.py   # OSM hospital search
│   ├── police_finder.py     # OSM police station search
│   ├── notification_service.py # SMS + Email
│   ├── whatsapp_service.py  # WhatsApp API
│   └── report_generator.py  # PDF/HTML police reports
└── reports/                 # Generated reports
```

---

## 🔧 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | Main dashboard |
| GET | `/video_feed` | MJPEG video stream |
| POST | `/api/connect_stream` | Connect IP webcam |
| POST | `/api/disconnect_stream` | Disconnect stream |
| POST | `/api/simulate_accident` | Trigger demo accident |
| GET | `/api/accidents` | List all accidents |
| POST | `/api/nearby_hospitals` | Find hospitals by lat/lng |
| POST | `/api/nearby_police` | Find police stations |
| GET | `/api/generate_report/<id>` | Download police report |
| POST | `/api/send_whatsapp` | Send WhatsApp alert |
| POST | `/api/get_location` | Geocode/reverse geocode |
| GET | `/api/status` | System status |

---

## 🎮 Demo Mode

No camera? Use **Simulate Accident** button to:
- Trigger accident detection event
- See hospital + police finder in action
- Test notification system
- Generate sample police report

---

## 🔒 Security Notes

- Never commit `.env` to version control
- Use strong `FLASK_SECRET_KEY` in production
- Run behind reverse proxy (nginx) in production
- Use HTTPS for production deployment

---

## 📜 License

MIT License — Free for educational and emergency response use.

---

## 🙏 Credits

- **OpenStreetMap** + Overpass API for hospital/police data
- **Twilio** for SMS + WhatsApp
- **OpenCV** for computer vision
- **Flask + SocketIO** for real-time communication
- **Google Maps** for map embeds

---

## 👨‍💻 Author
Chethan Kumar

GitHub: @ChethanKumar485

---
## ⭐ Support

If you like this project, give it a ⭐ on GitHub!" 🚀

