import cv2
import json

# Load YOLO output JSON
with open("/Users/kushal/intel/videos/output_gp_pro_test2_1.json", "r") as f:
    data = json.load(f)

# Open the video file
video_path = "/Users/kushal/intel/videos/gopro_test2.mp4"
cap = cv2.VideoCapture(video_path)

width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
fps = cap.get(cv2.CAP_PROP_FPS)
frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

output_path = "output.mp4"
fourcc = cv2.VideoWriter_fourcc(*"mp4v")
out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))

def get_detections_for_frame(current_timestamp):
    closest_entry = min(data, key=lambda entry: abs(entry["timestamp"] - current_timestamp))
    if abs(closest_entry["timestamp"] - current_timestamp) < 2000000:  # 2ms threshold
        return closest_entry["objects"], closest_entry["resolution"]["width"], closest_entry["resolution"]["height"]
    return [], width, height

while cap.isOpened():
    ret, frame = cap.read()
    if not ret:
        break

    # Get current timestamp in nanoseconds
    current_timestamp = int(cap.get(cv2.CAP_PROP_POS_MSEC) * 1e6)

    # Get detected objects for this timestamp
    objects, json_width, json_height = get_detections_for_frame(current_timestamp)

    for obj in objects:
        detection = obj["detection"]
        bbox = detection["bounding_box"]

        # Convert bounding box coordinates
        x_min = int(bbox["x_min"] * json_width * width / json_width)
        x_max = int(bbox["x_max"] * json_width * width / json_width)
        y_min = int(bbox["y_min"] * json_height * height / json_height)
        y_max = int(bbox["y_max"] * json_height * height / json_height)

        label = detection["label"]
        confidence = detection["confidence"]

        # Draw bounding box
        cv2.rectangle(frame, (x_min, y_min), (x_max, y_max), (0, 255, 0), 2)

        # Put label and confidence
        label_text = f"{label} ({confidence:.2f})"
        cv2.putText(frame, label_text, (x_min, y_min - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)

    # Write frame
    out.write(frame)

    # Display frame (press 'q' to exit early)
    cv2.imshow("Video", frame)
    if cv2.waitKey(1) & 0xFF == ord("q"):
        break

# Release resources
cap.release()
out.release()
cv2.destroyAllWindows()

print(f"Processing complete! Output saved as {output_path}")
