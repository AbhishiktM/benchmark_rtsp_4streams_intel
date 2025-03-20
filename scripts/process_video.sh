#!/bin/bash

# Default values (optional parameters)
DETECT_MODEL_PATH=""
POSE_MODEL_PATH=""
TRACK_MODEL_PATH=""
VIDEO_PATH=""
PROCESSING=""

# Parse named arguments
while [[ "$#" -gt 0 ]]; do
    case $1 in
        --video) VIDEO_PATH="$2"; shift ;;
        --tasks) PROCESSING="$2"; shift ;;
        --detect-model) DETECT_MODEL_PATH="$2"; shift ;;
        --pose-model) POSE_MODEL_PATH="$2"; shift ;;  
        --track-model) TRACK_MODEL_PATH="$2"; shift ;;
        *) echo "Unknown parameter: $1"; exit 1 ;;
    esac
    shift
done

echo "DEBUG: VIDEO_PATH='$VIDEO_PATH'"
echo "DEBUG: PROCESSING='$PROCESSING'"
echo "DEBUG: DETECT_MODEL_PATH='$DETECT_MODEL_PATH'"
echo "DEBUG: POSE_MODEL_PATH='$POSE_MODEL_PATH'"
echo "DEBUG: TRACK_MODEL_PATH='$TRACK_MODEL_PATH'"

# Validate required arguments
if [[ -z "$VIDEO_PATH" || -z "$PROCESSING" ]]; then
    echo "Usage: $0 --video <video_path> --tasks '<task_list>' [--detect-model <path>] [--pose-model <path>] [--track-model <path>]"
    exit 1
fi

echo "Processing video: $VIDEO_PATH with tasks: $PROCESSING with pose model: $POSE_MODEL_PATH"

# Sanitize task list
PROCESSING=$(echo "$PROCESSING" | tr -d '[]"')
PROCESSING=$(echo "$PROCESSING" | sed "s/,/ /g" | tr -d "'")
echo "DEBUG: PROCESSING=\"$PROCESSING\""

# Loop through each task and execute sequentially with PID tracking
for task in $PROCESSING; do
    echo "DEBUG: Processing task: $task"

    # Send Kafka message that the task is starting
    python3 ./scripts/define_video_boundary_kafka.py --video "$VIDEO_PATH" --task "$task" --status "start"

    PID=""

    if [[ "$task" == "gvadetect" && -n "$DETECT_MODEL_PATH" ]]; then
        PIPELINE="gst-launch-1.0 filesrc location=$VIDEO_PATH ! decodebin ! gvadetect model=$DETECT_MODEL_PATH device=CPU pre-process-backend=ie ! queue ! gvametaconvert add-tensor-data=true ! gvametapublish file-format=json-lines method=kafka address=kafka:9092 topic=dlstreamer_output ! fakesink async=false"
        echo "Running DL Streamer Pipeline for detection: $PIPELINE"
        eval "$PIPELINE" &
        PID=$!
    fi

    if [[ "$task" == "gvatrack" ]]; then
        PIPELINE="gst-launch-1.0 filesrc location=$VIDEO_PATH ! decodebin ! gvatrack tracking-type=short-term-imageless ! queue ! gvametaconvert add-tensor-data=true ! gvametapublish file-format=json-lines method=kafka address=kafka:9092 topic=dlstreamer_output ! fakesink async=false"
        echo "Running DL Streamer Pipeline for tracking: $PIPELINE"
        eval "$PIPELINE" &
        PID=$!
    fi

    if [[ "$task" == "gvapose" ]]; then
        echo "Triggering Pose Estimation..."
        python3 ./scripts/pose_estimation.py --video "$VIDEO_PATH" --model "$POSE_MODEL_PATH" --kafka-broker "kafka:9092" --kafka-topic "dlstreamer_output" &
        PID=$!
    fi

    # Wait for the process to complete before sending the end message
    if [[ -n "$PID" ]]; then
        wait "$PID"
        python3 ./scripts/define_video_boundary_kafka.py --video "$VIDEO_PATH" --task "$task" --status "end"
    fi
done

echo "All tasks for $VIDEO_PATH completed."
