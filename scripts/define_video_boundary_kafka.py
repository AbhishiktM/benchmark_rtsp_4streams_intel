#!/usr/bin/env python3

import argparse
import json
import time
from confluent_kafka import Producer

def send_kafka_message(video, task, status, camera=None, kafka_broker="kafka:9092", kafka_topic="dlstreamer-output"):
    conf = {'bootstrap.servers': kafka_broker}
    producer = Producer(conf)

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

    def delivery_report(err, msg):
        if err is not None:
            print(f'Message delivery failed: {err}')
        else:
            print(f'Message delivered to {msg.topic()} [{msg.partition()}]')

    producer.produce(kafka_topic, json.dumps(message), callback=delivery_report)
    producer.flush()
    print(f"Sent Kafka message: {message}")

def send_boundary_messages(action, cameras, kafka_broker, kafka_topic):
    """Send boundary messages for multiple cameras"""
    camera_list = cameras.split(',')
    
    for camera in camera_list:
        camera = camera.strip()
        send_kafka_message(
            video=f"{camera}_stream",
            task="boundary",
            status=action,
            camera=camera,
            kafka_broker=kafka_broker,
            kafka_topic=kafka_topic
        )

def main():
    parser = argparse.ArgumentParser(description="Send video boundary messages to Kafka")
    parser.add_argument("--action", required=True, choices=["start", "stop"], 
                       help="Action type: start or stop")
    parser.add_argument("--cameras", required=True, 
                       help="Comma-separated list of camera names")
    parser.add_argument("--kafka-broker", default="kafka:9092", 
                       help="Kafka broker address")
    parser.add_argument("--kafka-topic", default="dlstreamer-output", 
                       help="Kafka topic name")
    
    args = parser.parse_args()
    
    send_boundary_messages(args.action, args.cameras, args.kafka_broker, args.kafka_topic)

if __name__ == "__main__":
    main()
