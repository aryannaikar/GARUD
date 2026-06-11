from ultralytics import YOLO


class YOLODetector:
    def __init__(self, model_path="yolov8s.pt"):
        """
        Initialize YOLO model
        """
        print("[INFO] Loading YOLO model...")
        self.model = YOLO(model_path)
        print("[INFO] YOLO model loaded successfully.")

    def detect(self, frame):
        """
        Run YOLO detection on a frame.

        Returns:
            results: YOLO results object
        """
        results = self.model(frame)
        return results

    def get_detections(self, results):
        """
        Extract object names and confidence scores.

        Returns:
            detections: list of dictionaries
        """
        detections = []

        result = results[0]

        for box in result.boxes:
            class_id = int(box.cls[0])
            confidence = float(box.conf[0])

            class_name = self.model.names[class_id]

            detections.append({
                "class_name": class_name,
                "confidence": confidence
            })

        return detections

    def draw_detections(self, results):
        """
        Draw bounding boxes and labels.

        Returns:
            annotated_frame
        """
        return results[0].plot()