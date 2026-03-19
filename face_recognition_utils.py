import cv2
import numpy as np

# face_recognition is optional because it depends on dlib, which can be
# difficult to build on Windows.  Wrap import so the server can start even if
# the package isn't installed; downstream methods will check for None.
try:
    import face_recognition
except ImportError:
    face_recognition = None
    print("[FaceRecognition] warning: face_recognition package not available")

from ultralytics import YOLO

class FaceRecognition:
    def __init__(self):
        # load YOLO model; use the short name so the weights are downloaded if
        # not already present.  wrap in try/except so the app can still start
        # if the model fails to load.
        try:
            self.yolo_model = YOLO("yolov8n")
        except Exception as e:
            print(f"[FaceRecognition] could not load YOLO model: {e}")
            self.yolo_model = None
        self.known_face_encodings = []
        self.known_face_names = []
        self.known_face_ids = []
        self.frame_skip = 2
        self.frame_count = 0
    
    def reload_faces(self, persons):
        """Reload known faces from database"""
        self.known_face_encodings = []
        self.known_face_names = []
        self.known_face_ids = []
        
        for person in persons:
            if person['face_encoding'] is not None:
                self.known_face_encodings.append(person['face_encoding'])
                self.known_face_names.append(person['name'])
                self.known_face_ids.append(person['id'])
        
        print(f"Loaded {len(self.known_face_names)} faces")
    
    def register_face(self, image):
        """Extract face encoding from image for registration"""
        if face_recognition is None:
            return False, None

        # Convert BGR to RGB
        rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        
        # Detect face
        face_locations = face_recognition.face_locations(rgb_image)
        
        if not face_locations:
            return False, None
        
        # Get face encoding
        face_encodings = face_recognition.face_encodings(rgb_image, face_locations)
        
        if not face_encodings:
            return False, None
        
        return True, face_encodings[0]
    
    def process_frame(self, frame):
        """Process frame and return annotated frame and detections"""
        detections = []
        
        # Skip frames for performance
        self.frame_count += 1
        if self.frame_count % self.frame_skip != 0:
            return frame, detections

        # logging for diagnostics
        # print current known count and frame info
        # (this will print many lines; remove or comment out in production)
        # print(f"[FaceRecognition] processing frame (known faces: {len(self.known_face_names)})")
        
        # Run YOLO detection (skip if model unavailable)
        if self.yolo_model is None:
            return frame, detections
        results = self.yolo_model(frame)
        
        for result in results:
            boxes = result.boxes
            for box in boxes:
                if int(box.cls) == 0:  # Person class
                    x1, y1, x2, y2 = map(int, box.xyxy[0])
                    confidence = float(box.conf[0])
                    
                    # Extract person region
                    person_frame = frame[y1:y2, x1:x2]
                    
                    if person_frame.size > 0:
                        # Resize for faster face detection
                        height, width = person_frame.shape[:2]
                        if height > 0 and width > 0:
                            # Scale factor for face detection
                            scale = 0.5
                            small_frame = cv2.resize(person_frame, (0, 0), fx=scale, fy=scale)
                            
                            # Convert to RGB
                            rgb_small_frame = cv2.cvtColor(small_frame, cv2.COLOR_BGR2RGB)
                            
                            # Detect faces (skip if face_recognition missing)
                            if face_recognition is None:
                                cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 165, 255), 2)
                                cv2.putText(frame, "Face lib missing", (x1, y1-10), 
                                          cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 165, 255), 2)
                                continue

                            face_locations = face_recognition.face_locations(rgb_small_frame)
                            
                            if face_locations:
                                # Scale back face locations
                                top, right, bottom, left = face_locations[0]
                                top = int(top / scale) + y1
                                right = int(right / scale) + x1
                                bottom = int(bottom / scale) + y1
                                left = int(left / scale) + x1
                                
                                # Get face encoding
                                face_encoding = face_recognition.face_encodings(
                                    rgb_small_frame, [face_locations[0]]
                                )
                                
                                if face_encoding and self.known_face_encodings:
                                    # Compare with known faces
                                    name, match_confidence = self.match_face(face_encoding[0])
                                    
                                    if name != "Unknown":
                                        detections.append({
                                            'name': name,
                                            'confidence': match_confidence,
                                            'bbox': (x1, y1, x2, y2),
                                            'face_bbox': (left, top, right, bottom)
                                        })
                                        
                                        # Draw bounding boxes
                                        cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
                                        cv2.rectangle(frame, (left, top), (right, bottom), (255, 255, 0), 2)
                                        
                                        # Draw name and confidence
                                        label = f"{name} ({match_confidence:.2f})"
                                        cv2.putText(frame, label, (x1, y1-10), 
                                                  cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
                                    else:
                                        cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 0, 255), 2)
                                        cv2.rectangle(frame, (left, top), (right, bottom), (255, 0, 0), 2)
                                        cv2.putText(frame, "Unknown", (x1, y1-10), 
                                                  cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)
                                else:
                                    cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 165, 255), 2)
                                    cv2.putText(frame, "No face data", (x1, y1-10), 
                                              cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 165, 255), 2)
                            else:
                                cv2.rectangle(frame, (x1, y1), (x2, y2), (255, 165, 0), 2)
                                cv2.putText(frame, "No face", (x1, y1-10), 
                                          cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 165, 0), 2)
        
        return frame, detections
    
    def match_face(self, face_encoding):
        """Match face encoding with known faces"""
        if not self.known_face_encodings:
            return "Unknown", 0.0
        
        # Calculate face distances
        face_distances = face_recognition.face_distance(
            self.known_face_encodings, face_encoding
        )
        
        # Find best match
        best_match_index = np.argmin(face_distances)
        best_match_distance = face_distances[best_match_index]
        
        # Convert distance to confidence (closer distance = higher confidence)
        confidence = 1 - best_match_distance
        
        # Threshold for recognition
        if confidence > 0.4:  # Adjust threshold as needed
            return self.known_face_names[best_match_index], confidence
        else:
            return "Unknown", confidence