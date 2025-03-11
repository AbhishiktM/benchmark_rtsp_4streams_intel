import os
import subprocess
from kafka import KafkaConsumer, KafkaProducer
import json

KAFKA_BROKER = os.getenv("KAFKA_BROKER", "kafka:9092")
REQUEST_TOPIC = "dlstreamer_requests"
RESULT_TOPIC = "dlstreamer_output"

print(f"Connecting to Kafka at {KAFKA_BROKER}...")

try:
    consumer = KafkaConsumer(
        REQUEST_TOPIC,
        bootstrap_servers=[KAFKA_BROKER],
        value_deserializer=lambda m: json.loads(m.decode("utf-8")),
        auto_offset_reset="earliest",
        enable_auto_commit=True,
    )
    print(f"Connected to Kafka topic: {REQUEST_TOPIC}")

    producer = KafkaProducer(
        bootstrap_servers=[KAFKA_BROKER],
        value_serializer=lambda m: json.dumps(m).encode("utf-8"),
    )

    for message in consumer:
        job = message.value
        print("Received job:", job)

        video_file = job.get("video_file")
        processing = job.get("processing", ["gvadetect"])
        model = job.get("model", "/home/dlstreamer/models/public/yolo11s/FP32/yolo11s.xml")

        if not video_file:
            print("⚠️ No video file specified!")
            continue

        print(f" Sending {video_file} for processing with {processing}")

        # Run the script inside dlstreamer container
        cmd = f"bash /home/dlstreamer/scripts/process_video.sh {video_file} \"{processing}\" {model}"
        try:
            subprocess.run(cmd, shell=True, check=True)
            print(f"Video {video_file} processed successfully!")

            # Send success message to Kafka
            producer.send(RESULT_TOPIC, {"message": f"Processing completed for {video_file}"})
            print(f"Sent result to Kafka topic: {RESULT_TOPIC}")

        except subprocess.CalledProcessError as e:
            print(f"Error running processing script: {e}")
            producer.send(RESULT_TOPIC, {"error": f"Processing failed for {video_file}-------{e}"})

except Exception as e:
    print(f"Kafka Consumer Error: {e}")
