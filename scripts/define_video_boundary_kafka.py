#!/usr/bin/env python3

import json
import argparse
from datetime import datetime
from kafka import KafkaProducer

def send_boundary_message(action, cameras, kafka_broker, kafka_topic):
    """Send boundary message to Kafka"""
    
    try:
        producer = KafkaProducer(
            bootstrap_servers=[kafka_broker],
            value_serializer=lambda x: json.dumps(x).encode('utf-8')
        )
        
        camera_list = cameras.split(',')
        timestamp = datetime.now().isoformat()
        
        for camera in camera_list:
            message = {
                "type": "boundary",
                "action": action,
                "camera": camera.strip(),
                "timestamp": timestamp,
                "message": f"Video processing {action} for camera {camera.strip()}"
            }
            
            producer.send(kafka_topic, value=message)
            print(f"Sent {action} message for camera {camera.strip()}")
        
        producer.flush()
        producer.close()
        
        print(f"All {action} messages sent successfully")
        
    except Exception as e:
        print(f"Error sending boundary messages: {e}")

def main():
    parser = argparse.ArgumentParser(description="Send video boundary messages to Kafka")
    parser.add_argument("--action", required=True, choices=["start", "stop"], 
                       help="Action type: start or stop")
    parser.add_argument("--cameras", required=True, 
                       help="Comma-separated list of camera names")
    parser.add_argument("--kafka-broker", required=True, 
                       help="Kafka broker address")
    parser.add_argument("--kafka-topic", required=True, 
                       help="Kafka topic name")
    
    args = parser.parse_args()
    
    send_boundary_message(args.action, args.cameras, args.kafka_broker, args.kafka_topic)

if __name__ == "__main__":
    main()
