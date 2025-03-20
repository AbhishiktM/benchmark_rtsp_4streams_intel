import cv2
import numpy as np
import json
import time
import argparse
from collections import deque
from ultralytics import YOLO
from kafka import KafkaProducer

def parse_arguments():
    parser = argparse.ArgumentParser(description="Run pose estimation and publish results to Kafka.")
    parser.add_argument("--video", required=True, help="Path to the video file.")
    parser.add_argument("--model", required=True, help="Path to the YOLO pose estimation model.")
    parser.add_argument("--kafka-broker", required=True, help="Kafka broker address (e.g., kafka:9092).")
    parser.add_argument("--kafka-topic", required=True, help="Kafka topic to publish results.")
    return parser.parse_args()

def create_kafka_producer(broker_address):
    """Initialize Kafka producer"""
    try:
        producer = KafkaProducer(
            bootstrap_servers=broker_address,
            value_serializer=lambda v: json.dumps(v).encode("utf-8")
        )
        print(f"Connected to Kafka at {broker_address}")
        return producer
    except Exception as e:
        print(f"Error connecting to Kafka: {e}")
        exit(1)

def main():
    args = parse_arguments()
    print("ARGS-------------------------", args)

    # Load YOLO pose estimation model
    pose_model = YOLO(args.model)

    # Initialize Kafka producer
    producer = create_kafka_producer(args.kafka_broker)

    # Open video file
    cap = cv2.VideoCapture(args.video)

    # Tracking hand positions
    hand_history = deque(maxlen=5)

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break

        # Run pose estimation model
        pose_results = pose_model(frame)
        
        frame_data = {
            "timestamp": time.time(),
            "frame_number": int(cap.get(cv2.CAP_PROP_POS_FRAMES)),
            "poses": []
        }

        # Extract keypoints
        if pose_results and hasattr(pose_results[0], "keypoints") and pose_results[0].keypoints is not None:
            keypoints = pose_results[0].keypoints.xy.cpu().numpy()
            if len(keypoints) > 0:
                for kp in keypoints[0]:  # Extract each keypoint
                    frame_data["poses"].append({"x": float(kp[0]), "y": float(kp[1])})

        # Publish only if keypoints were detected
        if frame_data["poses"]:
            producer.send(args.kafka_topic, frame_data)
            # print(f"Published frame {frame_data['frame_number']} to Kafka topic {args.kafka_topic}")

        # Display the video with keypoints (optional for debugging)
        for kp in frame_data["poses"]:
            cv2.circle(frame, (int(kp["x"]), int(kp["y"])), 5, (0, 255, 0), -1)
        
        # cv2.imshow("Pose Estimation", frame)
        # if cv2.waitKey(1) & 0xFF == ord('q'):
        #     break

    # Release resources
    cap.release()
    cv2.destroyAllWindows()
    producer.close()
    print("Pose estimation processing completed.")

if __name__ == "__main__":
    main()
