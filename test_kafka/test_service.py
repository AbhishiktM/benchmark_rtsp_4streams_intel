import logging
import time
from fastapi import FastAPI
from kafka import KafkaProducer
from typing import List, Optional
from pydantic import BaseModel
import json

# ✅ Enable Kafka Debug Logs
logging.basicConfig(level=logging.WARNING)

# ✅ Change Kafka broker to container name (inside Podman network)
KAFKA_BROKER = "kafka:9092"  # ✅ Inside Podman, use "kafka", NOT "localhost"
TOPIC = "dlstreamer_requests"

app = FastAPI()

# ✅ Retry Kafka connection
for attempt in range(10):
    try:
        producer = KafkaProducer(
            bootstrap_servers=[KAFKA_BROKER],
            value_serializer=lambda m: json.dumps(m).encode("utf-8"),
        )
        print("✅ Connected to Kafka!")
        break
    except Exception as e:
        print(f"❌ Kafka not available, retrying in 5s... (Attempt {attempt + 1}/10) | Error: {e}")
        time.sleep(5)
else:
    print("❌ Failed to connect to Kafka after 10 attempts.")
    exit(1)


class VideoProcessingRequest(BaseModel):
    video_file: str
    processing: List[str] = ["gvadetect"]
    detect_model: Optional[str] = None
    pose_model: Optional[str] = None
    track_model: Optional[str] = None  # Add this if tracking is needed
    camera_id: Optional[str] = None

@app.post("/send-job/")
async def send_job(request: VideoProcessingRequest):
    try:
        print(f"📤 Sending job to Kafka: {request.model_dump()}")

        # ✅ Use `.get(timeout=10)` to debug message sending
        future = producer.send(TOPIC, request.model_dump())
        record_metadata = future.get(timeout=10)

        print(f"✅ Sent message to Kafka: {record_metadata.topic}, Partition: {record_metadata.partition}, Offset: {record_metadata.offset}")

        return {
            "message": "Job sent successfully",
            "job": request.model_dump(),
            "kafka_metadata": {
                "topic": record_metadata.topic,
                "partition": record_metadata.partition,
                "offset": record_metadata.offset,
            },
        }
    except Exception as e:
        print(f"❌ Error sending message to Kafka: {e}")
        import traceback
        traceback.print_exc()
        return {"error": str(e)}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
