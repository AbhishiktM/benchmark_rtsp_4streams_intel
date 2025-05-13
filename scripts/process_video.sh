#!/bin/bash

# Default values (required parameters)
DETECT_MODEL_PATH=""
POSE_MODEL_PATH=""
TRACK_MODEL_PATH=""
VIDEO_PATH=""
PROCESSING=""
CAMERA_ID=""
LIVESTREAM=""

# Parse named arguments
while [[ "$#" -gt 0 ]]; do
    case $1 in
        --video) VIDEO_PATH="$2"; shift ;;
        --tasks) PROCESSING="$2"; shift ;;
        --detect-model) DETECT_MODEL_PATH="$2"; shift ;;
        --pose-model) POSE_MODEL_PATH="$2"; shift ;;  
        --track-model) TRACK_MODEL_PATH="$2"; shift ;;
        --camera-id) CAMERA_ID="$2"; shift ;;
        --livestream) LIVESTREAM="$2"; shift ;;
        *) echo "Unknown parameter: $1"; exit 1 ;;
    esac
    shift
done

echo "DEBUG: VIDEO_PATH='$VIDEO_PATH'"
echo "DEBUG: PROCESSING='$PROCESSING'"
echo "DEBUG: DETECT_MODEL_PATH='$DETECT_MODEL_PATH'"
echo "DEBUG: POSE_MODEL_PATH='$POSE_MODEL_PATH'"
echo "DEBUG: TRACK_MODEL_PATH='$TRACK_MODEL_PATH'"
echo "DEBUG: CAMERA_ID='$CAMERA_ID'"
echo "DEBUG: LIVESTREAM='$LIVESTREAM'"

# Validate required arguments
if [[ -z "$VIDEO_PATH" || -z "$PROCESSING" ]]; then
    echo "Usage: $0 --video <video_path> --tasks '<task_list>' [--detect-model <path>] [--pose-model <path>] [--track-model <path>] [--camera-id <id>]"
    exit 1
fi

echo "Processing video: $VIDEO_PATH with tasks: $PROCESSING with pose model: $POSE_MODEL_PATH"

# Sanitize task list
PROCESSING=$(echo "$PROCESSING" | tr -d '[]"')
PROCESSING=$(echo "$PROCESSING" | sed "s/,/ /g" | tr -d "'")
echo "DEBUG: PROCESSING=\"$PROCESSING\""

# Sanitize input lists
IFS=',' read -ra VIDEO_LIST <<< "$VIDEO_PATH"
IFS=',' read -ra CAMERA_LIST <<< "$CAMERA_ID"

# Validate input lengths
if [[ "${#VIDEO_LIST[@]}" -ne "${#CAMERA_LIST[@]}" ]]; then
    echo "Error: The number of videos and camera IDs must be the same."
    exit 1
fi


# Track which tasks are enabled
RUN_DETECT=false
RUN_POSE=false

for task in $PROCESSING; do
    if [[ "$task" == "gvadetect" ]]; then
        RUN_DETECT=true
    elif [[ "$task" == "gvapose" ]]; then
        RUN_POSE=true
    else
        echo "Invalid task '$task' ignored. Only 'gvadetect' and 'gvapose' are supported."
    fi
done

# Build combined pipeline
PIPELINE="gst-launch-1.0 "

# Loop to append branches
for i in "${!VIDEO_LIST[@]}"; do
    VIDEO="${VIDEO_LIST[$i]}"
    CAM_ID="${CAMERA_LIST[$i]}"
    # Send Kafka start messages
    $RUN_DETECT && python3 ./scripts/define_video_boundary_kafka.py --video "$VIDEO" --task "gvadetect" --status "start" --camera "$CAM_ID"
    $RUN_POSE && python3 ./scripts/define_video_boundary_kafka.py --video "$VIDEO" --task "gvapose" --status "start" --camera "$CAM_ID"

    DETECT_TAG="{\"camera\": \"$CAM_ID\", \"video\": \"$VIDEO\", \"task\": \"gvadetect\"}"
    POSE_TAG="{\"camera\": \"$CAM_ID\", \"video\": \"$VIDEO\", \"task\": \"gvapose\"}"

    # Append detection pipeline
    if [[ "$LIVESTREAM" == "true" ]]; then
        if $RUN_DETECT && $RUN_POSE; then
            # Combined pipeline (single source, both models sequentially)
            PIPELINE+="v4l2src device=$VIDEO ! decodebin ! "
            PIPELINE+="gvadetect model=$DETECT_MODEL_PATH device=CPU pre-process-backend=ie ! queue ! "
            PIPELINE+="gvadetect model=$POSE_MODEL_PATH device=CPU pre-process-backend=opencv ! queue ! "
            PIPELINE+="gvametaconvert format=json tags='$POSE_TAG' ! "
            PIPELINE+="gvametapublish file-format=json-lines method=kafka address=kafka:9092 topic=dlstreamer_output ! fakesink "
        
        elif $RUN_DETECT; then
            # Only detection branch
            PIPELINE+="v4l2src device=$VIDEO ! decodebin ! "
            PIPELINE+="gvadetect model=$DETECT_MODEL_PATH device=CPU pre-process-backend=ie ! queue ! "
            PIPELINE+="gvametaconvert add-tensor-data=true tags='$DETECT_TAG' ! "
            PIPELINE+="gvametapublish file-format=json-lines method=kafka address=kafka:9092 topic=dlstreamer_output ! fakesink "

        elif $RUN_POSE; then
            # Only pose branch
            PIPELINE+="v4l2src device=$VIDEO ! decodebin ! "
            PIPELINE+="gvadetect model=$POSE_MODEL_PATH device=CPU pre-process-backend=opencv ! queue ! "
            PIPELINE+="gvametaconvert format=json tags='$POSE_TAG' ! "
            PIPELINE+="gvametapublish file-format=json-lines method=kafka address=kafka:9092 topic=dlstreamer_output ! fakesink "
        fi

    else
        # File-based pipeline
        if $RUN_DETECT; then
            PIPELINE+="filesrc location=$VIDEO ! decodebin ! "
            PIPELINE+="gvadetect model=$DETECT_MODEL_PATH device=CPU pre-process-backend=ie ! queue ! "
            PIPELINE+="gvametaconvert add-tensor-data=true tags='$DETECT_TAG' ! "
            PIPELINE+="gvametapublish file-format=json-lines method=kafka address=kafka:9092 topic=dlstreamer_output ! fakesink "
        fi

        if $RUN_POSE; then
            PIPELINE+="filesrc location=$VIDEO ! decodebin3 ! "
            PIPELINE+="gvadetect model=$POSE_MODEL_PATH device=CPU pre-process-backend=opencv ! queue ! "
            PIPELINE+="gvametaconvert format=json tags='$POSE_TAG' ! "
            PIPELINE+="gvametapublish file-format=json-lines method=kafka address=kafka:9092 topic=dlstreamer_output ! fakesink "
        fi
    fi


echo "Running unified DL Streamer pipeline:"
echo "$PIPELINE"

# Execute pipeline
eval "$PIPELINE"
STATUS=$?
echo "Status - $STATUS"

# Send Kafka end messages
# Send Kafka end messages per pair
if [[ "$STATUS" -eq 0 ]]; then
    for i in "${!VIDEO_LIST[@]}"; do
        VIDEO="${VIDEO_LIST[$i]}"
        CAM_ID="${CAMERA_LIST[$i]}"
        $RUN_DETECT && python3 ./scripts/define_video_boundary_kafka.py --video "$VIDEO" --task "gvadetect" --status "end" --camera "$CAM_ID"
        $RUN_POSE && python3 ./scripts/define_video_boundary_kafka.py --video "$VIDEO" --task "gvapose" --status "end" --camera "$CAM_ID"
    done

    echo "All tasks for $VIDEO_PATH completed successfully."
else
    echo "DL Streamer pipeline failed with exit code $STATUS."
fi
