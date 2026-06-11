import cv2
from detectors.yolo_detector import YOLODetector


def main():
    # Initialize detector
    detector = YOLODetector()

    # Open webcam
    camera = cv2.VideoCapture(0)

    if not camera.isOpened():
        print("[ERROR] Could not open webcam.")
        return

    print("[INFO] Press 'Q' to quit.\n")

    while True:
        success, frame = camera.read()

        if not success:
            print("[ERROR] Could not read frame.")
            break

        # Run YOLO
        results = detector.detect(frame)

        # Extract detections
        detections = detector.get_detections(results)

        # Print detections
        if detections:
            print("\nObjects Detected:")
            for obj in detections:
                print(
                    f"- {obj['class_name']} "
                    f"({obj['confidence']:.2f})"
                )

        # Draw boxes
        annotated_frame = detector.draw_detections(results)

        # Display output
        cv2.imshow("Garud Vision", annotated_frame)

        # Quit on Q
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    camera.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()