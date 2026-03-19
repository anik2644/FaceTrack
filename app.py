from flask import Flask, render_template, Response, request, jsonify
from flask_socketio import SocketIO
import cv2
import numpy as np
import pickle
import base64
from datetime import datetime
import threading
import time
import os
from database import AttendanceDB
from face_recognition_utils import FaceRecognition

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-here'
app.config['UPLOAD_FOLDER'] = 'uploads'
socketio = SocketIO(app, cors_allowed_origins="*")

# Create upload folder if not exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Global variables
camera = None
attendance_active = False
db = AttendanceDB()
face_recognizer = FaceRecognition()
attendance_log = []

# Threaded frame buffer for low-latency streaming
latest_frame = None
frame_lock = threading.Lock()
capture_thread = None

def capture_frames():
    """Background thread: continuously reads frames from camera into buffer."""
    global camera, attendance_active, latest_frame
    while attendance_active and camera and camera.isOpened():
        success, frame = camera.read()
        if not success:
            time.sleep(0.01)
            continue
        with frame_lock:
            latest_frame = frame.copy()

def generate_frames():
    """Stream generator: processes latest buffered frame and yields MJPEG."""
    global attendance_active, attendance_log, latest_frame
    while attendance_active:
        with frame_lock:
            frame = latest_frame.copy() if latest_frame is not None else None

        if frame is None:
            time.sleep(0.01)
            continue

        # Process frame for face recognition
        processed_frame, detections = face_recognizer.process_frame(frame)

        # Mark attendance for detected faces
        for detection in detections:
            if detection['name'] != 'Unknown':
                person = db.get_person_by_name(detection['name'])
                if person and db.mark_attendance(person['id'], detection['confidence']):
                    log_entry = {
                        'name': detection['name'],
                        'time': datetime.now().strftime('%H:%M:%S'),
                        'confidence': round(detection['confidence'], 2)
                    }
                    attendance_log.append(log_entry)

        # Encode frame with lower quality for speed (60% still looks good)
        encode_params = [cv2.IMWRITE_JPEG_QUALITY, 60]
        ret, buffer = cv2.imencode('.jpg', processed_frame, encode_params)
        if not ret:
            continue
        frame_bytes = buffer.tobytes()

        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/register')
def register():
    return render_template('register.html')

@app.route('/attendance')
def attendance():
    return render_template('attendance.html')

@app.route('/report')
def report():
    return render_template('report.html')

@app.route('/api/persons', methods=['GET'])
def get_persons():
    persons = db.get_all_persons()
    return jsonify([{
        'id': p['id'],
        'name': p['name'],
        'department': p['department'],
        'employee_id': p['employee_id']
    } for p in persons])

@app.route('/api/attendance/today', methods=['GET'])
def get_today_attendance():
    attendance_data = db.get_today_attendance()
    return jsonify([{
        'name': row[0],
        'department': row[1],
        'employee_id': row[2],
        'time': row[3],
        'confidence': row[4]
    } for row in attendance_data])

@app.route('/api/attendance/report', methods=['POST'])
def get_attendance_report():
    data = request.json
    start_date = data.get('start_date')
    end_date = data.get('end_date')

    if not start_date or not end_date:
        return jsonify({'error': 'Please provide start and end dates'}), 400

    report_data = db.get_attendance_report(start_date, end_date)

    # Group by date
    grouped = {}
    for row in report_data:
        date = row[3]
        if date not in grouped:
            grouped[date] = []
        grouped[date].append({
            'name': row[0],
            'department': row[1],
            'employee_id': row[2],
            'time': row[4],
            'confidence': row[5]
        })

    return jsonify(grouped)

@app.route('/api/register', methods=['POST'])
def register_face():
    try:
        data = request.json
        name = data.get('name')
        department = data.get('department', '')
        employee_id = data.get('employee_id', '')
        image_data = data.get('image')

        if not name or not image_data:
            return jsonify({'success': False, 'error': 'Name and image required'})

        # Decode base64 image
        image_data = image_data.split(',')[1]
        image_bytes = base64.b64decode(image_data)

        # Convert to numpy array
        nparr = np.frombuffer(image_bytes, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

        # Detect and encode face
        success, encoding = face_recognizer.register_face(img)

        if not success:
            return jsonify({'success': False, 'error': 'No face detected in image. Please make sure your face is clearly visible.'})

        # Save to database
        success = db.add_person(name, encoding, department, employee_id)

        if success:
            face_recognizer.reload_faces(db.get_all_persons())
            return jsonify({'success': True, 'message': f'Successfully registered {name}'})
        else:
            return jsonify({'success': False, 'error': 'Name already exists in database'})

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/capture_snapshot', methods=['POST'])
def capture_snapshot():
    """Grab a single frame from RTSP camera server-side for registration."""
    try:
        data = request.json
        rtsp_url = data.get('rtsp_url', '')
        if not rtsp_url:
            return jsonify({'success': False, 'error': 'RTSP URL required'})

        # Open stream briefly to grab one frame
        cap = cv2.VideoCapture(rtsp_url, cv2.CAP_FFMPEG)
        cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
        cap.set(cv2.CAP_PROP_POS_FRAMES, 0)

        if not cap.isOpened():
            return jsonify({'success': False, 'error': 'Could not connect to RTSP stream. Check URL and network.'})

        # Read a few frames to let stream stabilize
        frame = None
        for _ in range(5):
            ret, f = cap.read()
            if ret:
                frame = f
        cap.release()

        if frame is None:
            return jsonify({'success': False, 'error': 'Could not read frame from RTSP stream'})

        # Encode to base64 JPEG
        _, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 85])
        img_b64 = base64.b64encode(buffer).decode('utf-8')
        return jsonify({'success': True, 'image': f'data:image/jpeg;base64,{img_b64}'})

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/start_attendance', methods=['POST'])
def start_attendance():
    global attendance_active, camera, attendance_log, latest_frame, capture_thread

    data = request.json
    camera_source = data.get('camera_source', 0)

    # Stop any existing stream
    attendance_active = False
    if capture_thread and capture_thread.is_alive():
        capture_thread.join(timeout=2)
    if camera:
        camera.release()
    latest_frame = None

    if camera_source == 'rtsp':
        rtsp_url = data.get('rtsp_url', '').strip()
        if not rtsp_url:
            return jsonify({'success': False, 'error': 'RTSP URL required'})
        # Use FFMPEG backend with low-latency options
        cap = cv2.VideoCapture(rtsp_url, cv2.CAP_FFMPEG)
    else:
        cap = cv2.VideoCapture(int(camera_source))

    # Minimize internal buffer to reduce latency
    cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)

    if not cap.isOpened():
        return jsonify({'success': False, 'error': 'Could not open camera / RTSP stream. Check URL and network.'})

    camera = cap
    attendance_active = True
    attendance_log.clear()

    # Reload faces before starting
    face_recognizer.reload_faces(db.get_all_persons())

    # Start background capture thread
    capture_thread = threading.Thread(target=capture_frames, daemon=True)
    capture_thread.start()

    return jsonify({'success': True})

@app.route('/api/stop_attendance', methods=['POST'])
def stop_attendance():
    global attendance_active, camera, latest_frame

    attendance_active = False
    time.sleep(0.1)  # Let threads exit
    if camera:
        camera.release()
        camera = None
    latest_frame = None

    return jsonify({'success': True})

@app.route('/video_feed')
def video_feed():
    return Response(generate_frames(),
                   mimetype='multipart/x-mixed-replace; boundary=frame')

# Additional utility endpoints
@app.route('/api/attendance/stats', methods=['GET'])
def attendance_stats():
    """Return counts used on the dashboard."""
    stats = db.get_attendance_stats()
    return jsonify(stats)

@app.route('/api/test_rtsp', methods=['POST'])
def test_rtsp():
    data = request.json
    url = data.get('url')
    if not url:
        return jsonify({'success': False, 'error': 'No URL provided'})
    cap = cv2.VideoCapture(url)
    if not cap.isOpened():
        return jsonify({'success': False, 'error': 'Could not open stream'})
    ret, _ = cap.read()
    cap.release()
    if not ret:
        return jsonify({'success': False, 'error': 'Failed to read frame'})
    return jsonify({'success': True})

@app.route('/api/model_status', methods=['GET'])
def model_status():
    """Return basic information about loaded models for debugging."""
    yolo_ok = face_recognizer.yolo_model is not None
    return jsonify({'yolo_loaded': yolo_ok, 'known_faces': len(face_recognizer.known_face_names)})

@app.route('/api/attendance_log')
def get_attendance_log():
    global attendance_log
    return jsonify(attendance_log[-20:])  # Return last 20 entries

@socketio.on('connect')
def handle_connect():
    print('Client connected')

@socketio.on('disconnect')
def handle_disconnect():
    print('Client disconnected')

if __name__ == '__main__':
    print("Starting VisionID Attendance Server...")
    socketio.run(app, debug=False, use_reloader=False, host='0.0.0.0', port=5000, allow_unsafe_werkzeug=True)