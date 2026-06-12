"""
FALCON - Smart Road Accident Detection System
Main Flask Application
"""
import os
import cv2
import base64
import json
import time
import threading
import requests
import numpy as np
from datetime import datetime
from flask import Flask, render_template, Response, jsonify, request, send_file
from flask_socketio import SocketIO, emit
from utils.accident_detector import AccidentDetector
from utils.location_service import LocationService
from utils.hospital_finder import HospitalFinder
from utils.police_finder import PoliceFinder
from utils.notification_service import NotificationService
from utils.report_generator import ReportGenerator
from utils.whatsapp_service import WhatsAppService

app = Flask(__name__)
app.config['SECRET_KEY'] = 'falcon-secret-2024'
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')

# Global state
detector = AccidentDetector()
location_service = LocationService()
hospital_finder = HospitalFinder()
police_finder = PoliceFinder()
notifier = NotificationService()
report_gen = ReportGenerator()
whatsapp = WhatsAppService()

camera_stream = None
stream_active = False
accident_log = []
last_accident_frame = None
camera_lock = threading.Lock()
# Stores the browser-provided GPS location (set via /api/set_location)
current_location = None

class IPWebcamStream:
    def __init__(self, url):
        self.url = url
        self.cap = None
        self.active = False
        self.frame = None
        self.lock = threading.Lock()

    def start(self):
        self.active = True
        thread = threading.Thread(target=self._read_frames, daemon=True)
        thread.start()
        return self

    def _read_frames(self):
        self.cap = cv2.VideoCapture(self.url)
        while self.active:
            ret, frame = self.cap.read()
            if ret:
                with self.lock:
                    self.frame = frame
            else:
                time.sleep(0.1)
        if self.cap:
            self.cap.release()

    def get_frame(self):
        with self.lock:
            return self.frame.copy() if self.frame is not None else None

    def stop(self):
        self.active = False

ip_stream = None

def gen_frames():
    global last_accident_frame, accident_log
    frame_count = 0
    while stream_active:
        frame = None
        if ip_stream:
            frame = ip_stream.get_frame()

        if frame is None:
            time.sleep(0.05)
            continue

        frame_count += 1
        display_frame = frame.copy()

        # Run detection every 5 frames
        if frame_count % 5 == 0:
            result = detector.detect(frame)
            if result['accident_detected']:
                last_accident_frame = frame.copy()
                accident_data = handle_accident(frame, result)
                socketio.emit('accident_detected', accident_data)

        # Add HUD overlay
        display_frame = add_hud_overlay(display_frame, frame_count)

        ret, buffer = cv2.imencode('.jpg', display_frame, [cv2.IMWRITE_JPEG_QUALITY, 80])
        if ret:
            yield (b'--frame\r\nContent-Type: image/jpeg\r\n\r\n' + buffer.tobytes() + b'\r\n')
        time.sleep(0.033)

def add_hud_overlay(frame, frame_count):
    h, w = frame.shape[:2]
    overlay = frame.copy()

    # Top bar
    cv2.rectangle(overlay, (0, 0), (w, 50), (0, 0, 0), -1)
    frame = cv2.addWeighted(overlay, 0.6, frame, 0.4, 0)

    # FALCON text
    cv2.putText(frame, 'FALCON', (10, 35), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 200, 255), 2)
    cv2.putText(frame, 'ACCIDENT DETECTION ACTIVE', (130, 35), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 100), 1)

    # Time
    ts = datetime.now().strftime('%Y-%m-%d  %H:%M:%S')
    cv2.putText(frame, ts, (w - 300, 35), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (200, 200, 200), 1)

    # Scanning animation
    scan_x = int((frame_count * 4) % w)
    cv2.line(frame, (scan_x, 50), (scan_x, h), (0, 255, 0), 1)

    # Corner brackets
    color = (0, 200, 255)
    s = 30
    for (cx, cy) in [(50, 80), (w-50, 80), (50, h-30), (w-50, h-30)]:
        cv2.line(frame, (cx-s, cy), (cx+s, cy), color, 2)
        cv2.line(frame, (cx, cy-s), (cx, cy+s), color, 2)

    # Status dot
    cv2.circle(frame, (w-20, 20), 8, (0, 255, 0), -1)
    return frame

def handle_accident(frame, result):
    global accident_log, current_location
    timestamp = datetime.now()

    # Use browser-provided GPS location if available, else fall back to IP
    if current_location:
        loc = current_location
    else:
        loc = location_service.get_location()

    # Save accident frame
    frame_path = f"static/accidents/accident_{timestamp.strftime('%Y%m%d_%H%M%S')}.jpg"
    os.makedirs('static/accidents', exist_ok=True)
    cv2.imwrite(frame_path, frame)

    # Find nearby hospitals and police
    hospitals = hospital_finder.find_nearby(loc['lat'], loc['lng'], loc['address'])
    police_stations = police_finder.find_nearby(loc['lat'], loc['lng'], loc['address'])

    # Encode image for sending
    _, img_buf = cv2.imencode('.jpg', frame)
    img_b64 = base64.b64encode(img_buf.tobytes()).decode()

    accident_data = {
        'id': f"ACC_{timestamp.strftime('%Y%m%d%H%M%S')}",
        'timestamp': timestamp.isoformat(),
        'timestamp_readable': timestamp.strftime('%d %b %Y, %I:%M:%S %p'),
        'confidence': result['confidence'],
        'location': loc,
        'hospitals': hospitals,
        'police_stations': police_stations,
        'frame_path': frame_path,
        'frame_b64': img_b64,
        'severity': result.get('severity', 'HIGH')
    }

    accident_log.append(accident_data)

    # Send notifications in background
    threading.Thread(target=send_all_notifications, args=(accident_data,), daemon=True).start()

    return accident_data

def send_all_notifications(data):
    """Send notifications to hospitals, police, and WhatsApp"""
    # SMS/Email notifications
    for hospital in data['hospitals'][:3]:
        notifier.notify_hospital(hospital, data)
    
    for station in data['police_stations'][:2]:
        notifier.notify_police(station, data)

    # WhatsApp messages
    whatsapp.send_accident_alert(data)

    # Generate police report
    report_gen.generate_police_report(data)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/video_feed')
def video_feed():
    return Response(gen_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/api/connect_stream', methods=['POST'])
def connect_stream():
    global ip_stream, stream_active
    data = request.json
    url = data.get('url', '')

    # Support IP webcam formats
    if not url.startswith('http') and not url.startswith('rtsp'):
        url = f"http://{url}/video"

    try:
        # Stop any existing stream
        stream_active = False
        if ip_stream:
            ip_stream.stop()
        ip_stream = None
        time.sleep(0.3)

        # Start new stream
        new_stream = IPWebcamStream(url)
        new_stream.start()
        time.sleep(2)  # Wait for frames to buffer

        if new_stream.get_frame() is not None:
            ip_stream = new_stream
            stream_active = True
            return jsonify({'success': True, 'message': 'Stream connected successfully'})
        else:
            new_stream.stop()
            return jsonify({'success': False, 'message': 'Could not read from stream URL. Check IP and that IP Webcam app is running.'})
    except Exception as e:
        stream_active = False
        return jsonify({'success': False, 'message': str(e)})

@app.route('/api/disconnect_stream', methods=['POST'])
def disconnect_stream():
    global ip_stream, stream_active
    stream_active = False
    if ip_stream:
        ip_stream.stop()
        ip_stream = None
    return jsonify({'success': True})

@app.route('/api/simulate_accident', methods=['POST'])
def simulate_accident():
    """Simulate accident for demo purposes"""
    data = request.json or {}
    lat = data.get('lat', 12.9716)
    lng = data.get('lng', 77.5946)
    
    loc = {'lat': lat, 'lng': lng, 'address': f'Test Location ({lat:.4f}, {lng:.4f})', 'city': 'Bengaluru'}
    hospitals = hospital_finder.find_nearby(lat, lng, loc['address'])
    police_stations = police_finder.find_nearby(lat, lng, loc['address'])

    # Create demo frame
    frame = np.zeros((480, 640, 3), dtype=np.uint8)
    cv2.putText(frame, 'ACCIDENT DETECTED', (100, 240), cv2.FONT_HERSHEY_SIMPLEX, 1.5, (0, 0, 255), 3)
    _, buf = cv2.imencode('.jpg', frame)
    img_b64 = base64.b64encode(buf.tobytes()).decode()

    timestamp = datetime.now()
    accident_data = {
        'id': f"ACC_{timestamp.strftime('%Y%m%d%H%M%S')}",
        'timestamp': timestamp.isoformat(),
        'timestamp_readable': timestamp.strftime('%d %b %Y, %I:%M:%S %p'),
        'confidence': 0.94,
        'location': loc,
        'hospitals': hospitals,
        'police_stations': police_stations,
        'frame_b64': img_b64,
        'severity': 'HIGH'
    }
    accident_log.append(accident_data)
    socketio.emit('accident_detected', accident_data)
    threading.Thread(target=send_all_notifications, args=(accident_data,), daemon=True).start()
    return jsonify({'success': True, 'data': accident_data})

@app.route('/api/accidents')
def get_accidents():
    return jsonify(accident_log[-20:])

@app.route('/api/nearby_hospitals', methods=['POST'])
def nearby_hospitals():
    data = request.json
    results = hospital_finder.find_nearby(data.get('lat', 12.9716), data.get('lng', 77.5946), data.get('address',''))
    return jsonify(results)

@app.route('/api/nearby_police', methods=['POST'])
def nearby_police():
    data = request.json
    results = police_finder.find_nearby(data.get('lat', 12.9716), data.get('lng', 77.5946), data.get('address',''))
    return jsonify(results)

@app.route('/api/set_location', methods=['POST'])
def set_location():
    """Called by browser to persist the user's GPS location for accident detection"""
    global current_location
    data = request.json or {}
    lat = data.get('lat')
    lng = data.get('lng')
    if lat and lng:
        loc = location_service.reverse_geocode(lat, lng)
        current_location = loc
        return jsonify({'success': True, 'location': loc})
    return jsonify({'success': False, 'message': 'lat/lng required'}), 400

@app.route('/api/generate_report/<accident_id>')
def generate_report(accident_id):
    acc = next((a for a in accident_log if a['id'] == accident_id), None)
    if not acc:
        return jsonify({'error': 'Not found'}), 404
    path = report_gen.generate_police_report(acc)
    # Send as HTML so the embedded image and styles render correctly
    return send_file(path, mimetype='text/html', as_attachment=False,
                     download_name=f'Police_Report_{accident_id}.html')

@app.route('/api/approve_report/<accident_id>', methods=['POST'])
def approve_report(accident_id):
    """Police station approves the report — updates status in accident log"""
    acc = next((a for a in accident_log if a['id'] == accident_id), None)
    if not acc:
        return jsonify({'error': 'Not found'}), 404
    data = request.json or {}
    acc['approval'] = {
        'status': 'APPROVED',
        'approved_by': data.get('officer_name', 'Station Officer'),
        'station': data.get('station_name', 'Local Police Station'),
        'badge': data.get('badge', 'N/A'),
        'approved_at': datetime.now().strftime('%d %b %Y, %I:%M:%S %p'),
        'remarks': data.get('remarks', 'Cleared for hospital treatment. Proceed immediately.')
    }
    # Re-generate report with approval stamp
    report_gen.generate_police_report(acc)
    socketio.emit('report_approved', acc)
    return jsonify({'success': True, 'approval': acc['approval']})

@app.route('/api/send_whatsapp', methods=['POST'])
def send_whatsapp():
    data = request.json
    result = whatsapp.send_accident_alert(data)
    return jsonify(result)

@app.route('/api/get_location', methods=['POST'])
def get_location():
    data = request.json or {}
    lat = data.get('lat')
    lng = data.get('lng')
    if lat and lng:
        loc = location_service.reverse_geocode(lat, lng)
    else:
        loc = location_service.get_location()
    return jsonify(loc)

@app.route('/api/status')
def status():
    return jsonify({
        'stream_active': stream_active,
        'detection_active': detector.is_active(),
        'accidents_detected': len(accident_log),
        'uptime': time.time()
    })

if __name__ == '__main__':
    os.makedirs('static/accidents', exist_ok=True)
    os.makedirs('reports', exist_ok=True)
    socketio.run(app, host='0.0.0.0', port=5000, debug=False)