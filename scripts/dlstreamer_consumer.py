import os
import subprocess
from kafka import KafkaConsumer, KafkaProducer
from kafka.errors import CommitFailedError
import json
from time import sleep

KAFKA_BROKER = os.getenv("KAFKA_BROKER", "kafka:9092")
REQUEST_TOPIC = "dlstreamer_requests"
RESULT_TOPIC = "dlstreamer_output"

print(f"Connecting to Kafka at {KAFKA_BROKER}...")

try:
    sleep(10)

    consumer = KafkaConsumer(
        REQUEST_TOPIC,
        bootstrap_servers=[KAFKA_BROKER],
        group_id="dlstreamer_processor_group",
        value_deserializer=lambda m: json.loads(m.decode("utf-8")),
        auto_offset_reset="earliest",
        enable_auto_commit=False,
        max_poll_interval_ms=6000000,  # 100 minutes to prevent rebalance during long jobs
        session_timeout_ms=30000,
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
        detect_model = job.get("detect_model", "")
        pose_model = job.get("pose_model", "")
        track_model = job.get("track_model", "")
        camera_id = job.get("camera_id", "")
        livestream = job.get("livestream", "")

        if not video_file:
            print("No video file specified!")
            continue

        print(f"Sending {video_file} for processing with {processing}")

        cmd = f"bash /home/dlstreamer/scripts/process_video.sh --video {video_file} --tasks \"{processing}\" --detect-model {detect_model} --pose-model {pose_model} --track-model {track_model} --camera-id {camera_id} --livestream {livestream}"

        try:
            subprocess.run(cmd, shell=True, check=True)
            print(f"Video {video_file} processed successfully!")

            # Send success message to Kafka and flush
            producer.send(RESULT_TOPIC, {"message": f"Processing completed for {video_file}"})
            producer.flush()

            # Explicit commit after success
            consumer.commit()
            print("Kafka offset committed.")

        except subprocess.CalledProcessError as e:
            print(f"Error running processing script: {e}")
            producer.send(RESULT_TOPIC, {"error": f"Processing failed for {video_file}: {e}"})
            producer.flush()

        except CommitFailedError as ce:
            print(f"[WARN] Commit failed due to rebalance: {ce}")

except Exception as e:
    print(f"Kafka Consumer Error: {e}")
