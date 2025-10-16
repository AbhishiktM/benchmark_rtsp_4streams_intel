#!/usr/bin/env python3

import argparse
from confluent_kafka.admin import AdminClient, NewTopic

def create_topic(broker, topic_name, num_partitions=4, replication_factor=1):
    """Create Kafka topic if it doesn't exist"""
    
    admin_client = AdminClient({'bootstrap.servers': broker})
    
    # Check if topic exists
    metadata = admin_client.list_topics(timeout=10)
    if topic_name in metadata.topics:
        print(f"Topic '{topic_name}' already exists")
        return True
    
    # Create topic
    topic = NewTopic(
        topic_name, 
        num_partitions=num_partitions, 
        replication_factor=replication_factor
    )
    
    fs = admin_client.create_topics([topic])
    
    for topic, f in fs.items():
        try:
            f.result()
            print(f"Topic '{topic}' created successfully")
            return True
        except Exception as e:
            print(f"Failed to create topic '{topic}': {e}")
            return False

def main():
    parser = argparse.ArgumentParser(description="Create Kafka topic")
    parser.add_argument("--broker", default="kafka:9092", help="Kafka broker")
    parser.add_argument("--topic", required=True, help="Topic name")
    parser.add_argument("--partitions", type=int, default=4, help="Number of partitions")
    
    args = parser.parse_args()
    
    create_topic(args.broker, args.topic, args.partitions)

if __name__ == "__main__":
    main()
