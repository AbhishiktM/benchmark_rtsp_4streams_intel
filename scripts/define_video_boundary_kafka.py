import argparse
import json
from kafka import KafkaProducer
import time

def send_kafka_message(video, task, status, camera=None, kafka_broker="kafka:9092", kafka_topic="dlstreamer_output"):
    producer = KafkaProducer(
        bootstrap_servers=kafka_broker,
        value_serializer=lambda v: json.dumps(v).encode('utf-8')
    )

    message = {
        "video_id": video,
        "task": task,
        "status": status,
        "timestamp": time.time(),
        "tags": {
            "video": video,
            "task": task,
            "camera": camera
        }
    }

    producer.send(kafka_topic, message)
    producer.flush()
    print(f"Sent Kafka message: {message}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--video", required=True, help="Path to video file")
    parser.add_argument("--task", required=True, help="Processing task (e.g., detection, tracking, pose)")
    parser.add_argument("--status", required=True, choices=["start", "end"], help="Processing status")
    parser.add_argument("--kafka-broker", default="kafka:9092", help="Kafka broker address")
    parser.add_argument("--kafka-topic", default="dlstreamer_output", help="Kafka topic name")
    parser.add_argument("--camera", required=True, help="Camera ID (e.g., camera1)")


    args = parser.parse_args()
    send_kafka_message(args.video, args.task, args.status, args.camera, args.kafka_broker, args.kafka_topic)

