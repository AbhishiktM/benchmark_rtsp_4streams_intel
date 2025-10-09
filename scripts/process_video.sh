# #!/bin/bash

# # DLStreamer Video Processing Script with RTSP and Kafka Support
# # Supports both file-based and RTSP stream processing with OpenVINO inference

# set -e

# # Default values
# VIDEO=""
# TASKS=""
# DETECT_MODEL=""
# POSE_MODEL=""
# CAMERA_ID=""
# LIVESTREAM="false"
# OUTPUT_DIR="./output"
# KAFKA_BROKER="kafka:9092"
# KAFKA_TOPIC="dlstreamer_output"

# # Function to display usage
# usage() {
#     echo "Usage: $0 [OPTIONS]"
#     echo "Options:"
#     echo "  --video VIDEO_PATH          Path to video file or RTSP URL (comma-separated for multiple)"
#     echo "  --tasks TASKS               Tasks to run: gvadetect,gvapose (comma-separated)"
#     echo "  --detect-model MODEL_PATH   Path to detection model XML file"
#     echo "  --pose-model MODEL_PATH     Path to pose estimation model XML file"
#     echo "  --camera-id CAMERA_ID       Camera identifier (comma-separated for multiple)"
#     echo "  --livestream BOOLEAN        Enable livestream mode (true/false)"
#     echo "  --output-dir DIR            Output directory for results"
#     echo "  --kafka-broker BROKER       Kafka broker address (default: kafka:9092)"
#     echo "  --kafka-topic TOPIC         Kafka topic name (default: dlstreamer_output)"
#     echo "  --help                      Display this help message"
#     echo ""
#     echo "Examples:"
#     echo "  # Single RTSP stream with detection"
#     echo "  $0 --video 'rtsp://rtsp-server:8554/cam0' --tasks 'gvadetect' --detect-model './models/detection_model/FP32/det.xml' --camera-id 'cam0'"
#     echo ""
#     echo "  # Multiple RTSP streams with both detection and pose"
#     echo "  $0 --video 'rtsp://rtsp-server:8554/cam0,rtsp://rtsp-server:8554/cam2' --tasks 'gvadetect,gvapose' --detect-model './models/detection_model/FP32/det.xml' --pose-model './models/public/yolo11s-pose/FP32/yolo11s-pose.xml' --camera-id 'cam0,cam2'"
# }

# # Parse command line arguments
# while [[ $# -gt 0 ]]; do
#     case $1 in
#         --video)
#             VIDEO="$2"
#             shift 2
#             ;;
#         --tasks)
#             TASKS="$2"
#             shift 2
#             ;;
#         --detect-model)
#             DETECT_MODEL="$2"
#             shift 2
#             ;;
#         --pose-model)
#             POSE_MODEL="$2"
#             shift 2
#             ;;
#         --camera-id)
#             CAMERA_ID="$2"
#             shift 2
#             ;;
#         --livestream)
#             LIVESTREAM="$2"
#             shift 2
#             ;;
#         --output-dir)
#             OUTPUT_DIR="$2"
#             shift 2
#             ;;
#         --kafka-broker)
#             KAFKA_BROKER="$2"
#             shift 2
#             ;;
#         --kafka-topic)
#             KAFKA_TOPIC="$2"
#             shift 2
#             ;;
#         --help)
#             usage
#             exit 0
#             ;;
#         *)
#             echo "Unknown option: $1"
#             usage
#             exit 1
#             ;;
#     esac
# done

# # Validation
# if [[ -z "$VIDEO" ]]; then
#     echo "Error: --video is required"
#     usage
#     exit 1
# fi

# if [[ -z "$TASKS" ]]; then
#     echo "Error: --tasks is required"
#     usage
#     exit 1
# fi

# if [[ -z "$CAMERA_ID" ]]; then
#     echo "Error: --camera-id is required"
#     usage
#     exit 1
# fi

# # Parse comma-separated values
# IFS=',' read -ra VIDEO_LIST <<< "$VIDEO"
# IFS=',' read -ra TASK_LIST <<< "$TASKS"
# IFS=',' read -ra CAMERA_LIST <<< "$CAMERA_ID"

# # Validate that we have matching numbers of videos and camera IDs
# if [[ ${#VIDEO_LIST[@]} -ne ${#CAMERA_LIST[@]} ]]; then
#     echo "Error: Number of videos (${#VIDEO_LIST[@]}) must match number of camera IDs (${#CAMERA_LIST[@]})"
#     exit 1
# fi

# # Check if tasks are valid and models are provided
# RUN_DETECT=false
# RUN_POSE=false

# for task in "${TASK_LIST[@]}"; do
#     case $task in
#         gvadetect)
#             RUN_DETECT=true
#             if [[ -z "$DETECT_MODEL" ]]; then
#                 echo "Error: --detect-model is required for gvadetect task"
#                 exit 1
#             fi
#             if [[ ! -f "$DETECT_MODEL" ]]; then
#                 echo "Error: Detection model file not found: $DETECT_MODEL"
#                 exit 1
#             fi
#             ;;
#         gvapose)
#             RUN_POSE=true
#             if [[ -z "$POSE_MODEL" ]]; then
#                 echo "Error: --pose-model is required for gvapose task"
#                 exit 1
#             fi
#             if [[ ! -f "$POSE_MODEL" ]]; then
#                 echo "Error: Pose model file not found: $POSE_MODEL"
#                 exit 1
#             fi
#             ;;
#         *)
#             echo "Error: Unknown task: $task"
#             echo "Supported tasks: gvadetect, gvapose"
#             exit 1
#             ;;
#     esac
# done

# # Create output directory
# mkdir -p "$OUTPUT_DIR"

# # Function to check if hardware acceleration is available
# check_hardware_acceleration() {
#     if command -v vainfo >/dev/null 2>&1; then
#         if vainfo 2>/dev/null | grep -q "H264"; then
#             echo "vaapi"
#             return
#         fi
#     fi
    
#     if lspci 2>/dev/null | grep -i nvidia >/dev/null; then
#         if command -v nvidia-smi >/dev/null 2>&1; then
#             echo "cuda"
#             return
#         fi
#     fi
    
#     echo "software"
# }

# # Function to optimize RTSP pipeline based on source type
# optimize_source_pipeline() {
#     local video_path="$1"
#     local hw_accel="$2"
#     local base_pipeline=""
    
#     if [[ "$video_path" == rtsp://* ]]; then
#         echo "Setting up RTSP source for: $video_path" >&2
        
#         # RTSP stream - use rtspsrc with optimizations
#         base_pipeline="rtspsrc location=\"$video_path\" "
#         base_pipeline+="latency=0 buffer-mode=auto drop-on-latency=true "
#         base_pipeline+="protocols=tcp timeout=5000000 retry=3 ! "
#         base_pipeline+="rtph264depay ! h264parse ! "
        
#         # Choose decoder based on hardware acceleration
#         case $hw_accel in
#             vaapi)
#                 base_pipeline+="vaapih264dec ! videoconvert ! "
#                 echo "Using VAAPI hardware decoder for RTSP" >&2
#                 ;;
#             cuda)
#                 base_pipeline+="nvh264dec ! videoconvert ! "
#                 echo "Using NVIDIA hardware decoder for RTSP" >&2
#                 ;;
#             *)
#                 base_pipeline+="avdec_h264 max-threads=2 ! videoconvert ! "
#                 echo "Using software decoder for RTSP" >&2
#                 ;;
#         esac
        
#     elif [[ "$video_path" == http://* ]] || [[ "$video_path" == https://* ]]; then
#         echo "Setting up HTTP source for: $video_path" >&2
#         base_pipeline="souphttpsrc location=\"$video_path\" ! decodebin ! videoconvert ! "
        
#     else
#         echo "Setting up file source for: $video_path" >&2
#         # File-based source
#         if [[ ! -f "$video_path" ]]; then
#             echo "Error: Video file not found: $video_path" >&2
#             exit 1
#         fi
#         base_pipeline="filesrc location=\"$video_path\" ! decodebin ! videoconvert ! "
#     fi
    
#     echo "$base_pipeline"
# }

# # Function to build inference pipeline
# build_inference_pipeline() {
#     local source_pipeline="$1"
#     local camera_id="$2"
#     local video_path="$3"
#     local pipeline=""
    
#     # Create tags for Kafka messages
#     local detect_tag="{\\\"camera\\\": \\\"$camera_id\\\", \\\"video\\\": \\\"$video_path\\\", \\\"task\\\": \\\"gvadetect\\\"}"
#     local pose_tag="{\\\"camera\\\": \\\"$camera_id\\\", \\\"video\\\": \\\"$video_path\\\", \\\"task\\\": \\\"gvapose\\\"}"
    
#     if $RUN_DETECT && $RUN_POSE; then
#         echo "Building combined detection and pose pipeline for $camera_id" >&2
        
#         # Combined pipeline with tee for branching
#         pipeline="$source_pipeline tee name=t_$camera_id "
        
#         # Detection branch
#         pipeline+="t_$camera_id. ! queue max-size-buffers=10 leaky=downstream ! "
#         pipeline+="gvadetect model=\"$DETECT_MODEL\" device=CPU pre-process-backend=ie ! "
#         pipeline+="gvametaconvert add-tensor-data=true tags=\"$detect_tag\" ! "
#         pipeline+="gvametapublish file-format=json-lines method=kafka address=\"$KAFKA_BROKER\" topic=\"$KAFKA_TOPIC\" ! "
#         pipeline+="fakesink sync=false "
        
#         # Pose branch
#         pipeline+="t_$camera_id. ! queue max-size-buffers=10 leaky=downstream ! "
#         pipeline+="gvadetect model=\"$POSE_MODEL\" device=CPU pre-process-backend=opencv ! "
#         pipeline+="gvametaconvert format=json tags=\"$pose_tag\" ! "
#         pipeline+="gvametapublish file-format=json-lines method=kafka address=\"$KAFKA_BROKER\" topic=\"$KAFKA_TOPIC\" ! "
#         pipeline+="fakesink sync=false "
        
#     elif $RUN_DETECT; then
#         echo "Building detection-only pipeline for $camera_id" >&2
        
#         pipeline="$source_pipeline "
#         pipeline+="gvadetect model=\"$DETECT_MODEL\" device=CPU pre-process-backend=ie ! "
#         pipeline+="gvametaconvert add-tensor-data=true tags=\"$detect_tag\" ! "
#         pipeline+="gvametapublish file-format=json-lines method=kafka address=\"$KAFKA_BROKER\" topic=\"$KAFKA_TOPIC\" ! "
#         pipeline+="fakesink sync=false "
        
#     elif $RUN_POSE; then
#         echo "Building pose-only pipeline for $camera_id" >&2
        
#         pipeline="$source_pipeline "
#         pipeline+="gvadetect model=\"$POSE_MODEL\" device=CPU pre-process-backend=opencv ! "
#         pipeline+="gvametaconvert format=json tags=\"$pose_tag\" ! "
#         pipeline+="gvametapublish file-format=json-lines method=kafka address=\"$KAFKA_BROKER\" topic=\"$KAFKA_TOPIC\" ! "
#         pipeline+="fakesink sync=false "
#     fi
    
#     echo "$pipeline"
# }

# # Main execution
# echo "=== DLStreamer Video Processing Started ==="
# echo "Videos: ${VIDEO_LIST[*]}"
# echo "Tasks: ${TASK_LIST[*]}"
# echo "Camera IDs: ${CAMERA_LIST[*]}"
# echo "Kafka Broker: $KAFKA_BROKER"
# echo "Kafka Topic: $KAFKA_TOPIC"

# # Check hardware acceleration
# HW_ACCEL=$(check_hardware_acceleration)
# echo "Hardware acceleration: $HW_ACCEL"

# # Send start boundary messages to Kafka
# echo "Sending start boundary messages to Kafka..."
# for i in "${!VIDEO_LIST[@]}"; do
#     VIDEO_PATH="${VIDEO_LIST[$i]}"
#     CAM_ID="${CAMERA_LIST[$i]}"
    
#     if $RUN_DETECT; then
#         python3 ./scripts/define_video_boundary_kafka.py \
#             --video "$VIDEO_PATH" \
#             --task "gvadetect" \
#             --status "start" \
#             --camera "$CAM_ID" \
#             --kafka-broker "$KAFKA_BROKER" \
#             --kafka-topic "$KAFKA_TOPIC" || echo "Warning: Could not send detect start boundary for $CAM_ID"
#     fi
    
#     if $RUN_POSE; then
#         python3 ./scripts/define_video_boundary_kafka.py \
#             --video "$VIDEO_PATH" \
#             --task "gvapose" \
#             --status "start" \
#             --camera "$CAM_ID" \
#             --kafka-broker "$KAFKA_BROKER" \
#             --kafka-topic "$KAFKA_TOPIC" || echo "Warning: Could not send pose start boundary for $CAM_ID"
#     fi
# done

# # Build and execute pipelines
# if [[ ${#VIDEO_LIST[@]} -eq 1 ]]; then
#     # Single video processing
#     VIDEO_PATH="${VIDEO_LIST[0]}"
#     CAM_ID="${CAMERA_LIST[0]}"
    
#     echo "Processing single video: $VIDEO_PATH (Camera: $CAM_ID)"
    
#     SOURCE_PIPELINE=$(optimize_source_pipeline "$VIDEO_PATH" "$HW_ACCEL")
#     FULL_PIPELINE=$(build_inference_pipeline "$SOURCE_PIPELINE" "$CAM_ID" "$VIDEO_PATH")
    
#     echo "Executing pipeline..."
#     echo "Pipeline: $FULL_PIPELINE" >&2
    
#     gst-launch-1.0 $FULL_PIPELINE
    
# else
#     # Multiple video processing - create parallel pipelines
#     echo "Processing multiple videos in parallel..."
    
#     PIDS=()
    
#     for i in "${!VIDEO_LIST[@]}"; do
#         VIDEO_PATH="${VIDEO_LIST[$i]}"
#         CAM_ID="${CAMERA_LIST[$i]}"
        
#         echo "Starting pipeline for: $VIDEO_PATH (Camera: $CAM_ID)"
        
#         SOURCE_PIPELINE=$(optimize_source_pipeline "$VIDEO_PATH" "$HW_ACCEL")
#         FULL_PIPELINE=$(build_inference_pipeline "$SOURCE_PIPELINE" "$CAM_ID" "$VIDEO_PATH")
        
#         echo "Pipeline $i: $FULL_PIPELINE" >&2
        
#         # Run each pipeline in background
#         (
#             echo "Starting inference for camera $CAM_ID..."
#             gst-launch-1.0 $FULL_PIPELINE
#         ) &
        
#         PIDS+=($!)
        
#         # Small delay between starting pipelines to avoid resource contention
#         sleep 2
#     done
    
#     echo "All pipelines started. PIDs: ${PIDS[*]}"
#     echo "Waiting for pipelines to complete..."
    
#     # Wait for all background processes
#     for pid in "${PIDS[@]}"; do
#         wait $pid
#         echo "Pipeline with PID $pid completed"
#     done
# fi

# # Send end boundary messages to Kafka
# echo "Sending end boundary messages to Kafka..."
# for i in "${!VIDEO_LIST[@]}"; do
#     VIDEO_PATH="${VIDEO_LIST[$i]}"
#     CAM_ID="${CAMERA_LIST[$i]}"
    
#     if $RUN_DETECT; then
#         python3 ./scripts/define_video_boundary_kafka.py \
#             --video "$VIDEO_PATH" \
#             --task "gvadetect" \
#             --status "end" \
#             --camera "$CAM_ID" \
#             --kafka-broker "$KAFKA_BROKER" \
#             --kafka-topic "$KAFKA_TOPIC" || echo "Warning: Could not send detect end boundary for $CAM_ID"
#     fi
    
#     if $RUN_POSE; then
#         python3 ./scripts/define_video_boundary_kafka.py \
#             --video "$VIDEO_PATH" \
#             --task "gvapose" \
#             --status "end" \
#             --camera "$CAM_ID" \
#             --kafka-broker "$KAFKA_BROKER" \
#             --kafka-topic "$KAFKA_TOPIC" || echo "Warning: Could not send pose end boundary for $CAM_ID"
#     fi
# done

# echo "=== DLStreamer Video Processing Completed ==="

#!/bin/bash

# DLStreamer Video Processing Script with GPU/CPU Selection
set -e

# Default values
VIDEO=""
TASKS=""
DETECT_MODEL=""
POSE_MODEL=""
CAMERA_ID=""
LIVESTREAM="false"
OUTPUT_DIR="./output"
KAFKA_BROKER="kafka:9092"
KAFKA_TOPIC="dlstreamer_output"
DEVICE="CPU"  # Default to CPU
ENABLE_GPU="false"

# Function to display usage
usage() {
    echo "Usage: $0 [OPTIONS]"
    echo "Options:"
    echo "  --video VIDEO_PATH          Path to video file or RTSP URL (comma-separated for multiple)"
    echo "  --tasks TASKS               Tasks to run: gvadetect,gvapose (comma-separated)"
    echo "  --detect-model MODEL_PATH   Path to detection model XML file"
    echo "  --pose-model MODEL_PATH     Path to pose estimation model XML file"
    echo "  --camera-id CAMERA_ID       Camera identifier (comma-separated for multiple)"
    echo "  --device DEVICE             Processing device: CPU, GPU, AUTO (default: CPU)"
    echo "  --enable-gpu                Enable GPU acceleration if available"
    echo "  --livestream BOOLEAN        Enable livestream mode (true/false)"
    echo "  --output-dir DIR            Output directory for results"
    echo "  --kafka-broker BROKER       Kafka broker address (default: kafka:9092)"
    echo "  --kafka-topic TOPIC         Kafka topic name (default: dlstreamer_output)"
    echo "  --help                      Display this help message"
    echo ""
    echo "Examples:"
    echo "  # CPU processing (default)"
    echo "  $0 --video 'rtsp://rtsp-server:8554/cam0' --tasks 'gvadetect' --detect-model './models/detection_model/FP32/det.xml' --camera-id 'cam0'"
    echo ""
    echo "  # GPU processing"
    echo "  $0 --video 'rtsp://rtsp-server:8554/cam0' --tasks 'gvadetect' --detect-model './models/detection_model/FP32/det.xml' --camera-id 'cam0' --device GPU"
    echo ""
    echo "  # Auto device selection"
    echo "  $0 --video 'rtsp://rtsp-server:8554/cam0' --tasks 'gvadetect' --detect-model './models/detection_model/FP32/det.xml' --camera-id 'cam0' --device AUTO"
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --video)
            VIDEO="$2"
            shift 2
            ;;
        --tasks)
            TASKS="$2"
            shift 2
            ;;
        --detect-model)
            DETECT_MODEL="$2"
            shift 2
            ;;
        --pose-model)
            POSE_MODEL="$2"
            shift 2
            ;;
        --camera-id)
            CAMERA_ID="$2"
            shift 2
            ;;
        --device)
            DEVICE="$2"
            shift 2
            ;;
        --enable-gpu)
            ENABLE_GPU="true"
            DEVICE="GPU"
            shift
            ;;
        --livestream)
            LIVESTREAM="$2"
            shift 2
            ;;
        --output-dir)
            OUTPUT_DIR="$2"
            shift 2
            ;;
        --kafka-broker)
            KAFKA_BROKER="$2"
            shift 2
            ;;
        --kafka-topic)
            KAFKA_TOPIC="$2"
            shift 2
            ;;
        --help)
            usage
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            usage
            exit 1
            ;;
    esac
done

# Validation
if [[ -z "$VIDEO" ]]; then
    echo "Error: --video is required"
    usage
    exit 1
fi

if [[ -z "$TASKS" ]]; then
    echo "Error: --tasks is required"
    usage
    exit 1
fi

if [[ -z "$CAMERA_ID" ]]; then
    echo "Error: --camera-id is required"
    usage
    exit 1
fi

# Parse comma-separated values
IFS=',' read -ra VIDEO_LIST <<< "$VIDEO"
IFS=',' read -ra TASK_LIST <<< "$TASKS"
IFS=',' read -ra CAMERA_LIST <<< "$CAMERA_ID"

# Validate that we have matching numbers of videos and camera IDs
if [[ ${#VIDEO_LIST[@]} -ne ${#CAMERA_LIST[@]} ]]; then
    echo "Error: Number of videos (${#VIDEO_LIST[@]}) must match number of camera IDs (${#CAMERA_LIST[@]})"
    exit 1
fi

# Check if tasks are valid and models are provided
RUN_DETECT=false
RUN_POSE=false

for task in "${TASK_LIST[@]}"; do
    case $task in
        gvadetect)
            RUN_DETECT=true
            if [[ -z "$DETECT_MODEL" ]]; then
                echo "Error: --detect-model is required for gvadetect task"
                exit 1
            fi
            if [[ ! -f "$DETECT_MODEL" ]]; then
                echo "Error: Detection model file not found: $DETECT_MODEL"
                exit 1
            fi
            ;;
        gvapose)
            RUN_POSE=true
            if [[ -z "$POSE_MODEL" ]]; then
                echo "Error: --pose-model is required for gvapose task"
                exit 1
            fi
            if [[ ! -f "$POSE_MODEL" ]]; then
                echo "Error: Pose model file not found: $POSE_MODEL"
                exit 1
            fi
            ;;
        *)
            echo "Error: Unknown task: $task"
            echo "Supported tasks: gvadetect, gvapose"
            exit 1
            ;;
    esac
done

# Create output directory
mkdir -p "$OUTPUT_DIR"

# Function to detect available hardware acceleration
detect_hardware_acceleration() {
    local available_devices=()
    
    # Check for NVIDIA GPU
    if command -v nvidia-smi >/dev/null 2>&1; then
        if nvidia-smi >/dev/null 2>&1; then
            available_devices+=("NVIDIA_GPU")
            echo "NVIDIA GPU detected" >&2
        fi
    fi
    
    # Check for Intel GPU (VAAPI)
    if command -v vainfo >/dev/null 2>&1; then
        if vainfo 2>/dev/null | grep -q "H264"; then
            available_devices+=("INTEL_GPU")
            echo "Intel GPU (VAAPI) detected" >&2
        fi
    fi
    
    # Always have CPU as fallback
    available_devices+=("CPU")
    
    echo "${available_devices[@]}"
}

# Function to select optimal device
select_device() {
    local requested_device="$1"
    local available_devices=($(detect_hardware_acceleration))
    
    case $requested_device in
        AUTO)
            # Auto-select best available device
            for device in "${available_devices[@]}"; do
                case $device in
                    NVIDIA_GPU)
                        echo "GPU"
                        return
                        ;;
                    INTEL_GPU)
                        echo "GPU"
                        return
                        ;;
                esac
            done
            echo "CPU"
            ;;
        GPU)
            # Check if any GPU is available
            for device in "${available_devices[@]}"; do
                if [[ $device == *"GPU"* ]]; then
                    echo "GPU"
                    return
                fi
            done
            echo "Warning: GPU requested but not available, falling back to CPU" >&2
            echo "CPU"
            ;;
        CPU)
            echo "CPU"
            ;;
        *)
            echo "Warning: Unknown device '$requested_device', using CPU" >&2
            echo "CPU"
            ;;
    esac
}

# Function to optimize source pipeline based on device and source type
optimize_source_pipeline() {
    local video_path="$1"
    local device="$2"
    local base_pipeline=""
    
    if [[ "$video_path" == rtsp://* ]]; then
        echo "Setting up RTSP source for: $video_path (Device: $device)" >&2
        
        # RTSP stream - use rtspsrc with optimizations
        base_pipeline="rtspsrc location=\"$video_path\" "
        base_pipeline+="latency=0 buffer-mode=auto drop-on-latency=true "
        base_pipeline+="protocols=tcp timeout=5000000 retry=3 ! "
        base_pipeline+="rtph264depay ! h264parse ! "
        
        # Choose decoder based on device
        case $device in
            GPU)
                # Try NVIDIA decoder first, then VAAPI, then software
                if command -v nvidia-smi >/dev/null 2>&1 && nvidia-smi >/dev/null 2>&1; then
                    base_pipeline+="nvh264dec ! videoconvert ! "
                    echo "Using NVIDIA GPU decoder for RTSP" >&2
                elif command -v vainfo >/dev/null 2>&1 && vainfo 2>/dev/null | grep -q "H264"; then
                    base_pipeline+="vaapih264dec ! videoconvert ! "
                    echo "Using Intel GPU (VAAPI) decoder for RTSP" >&2
                else
                    base_pipeline+="avdec_h264 max-threads=4 ! videoconvert ! "
                    echo "GPU requested but not available, using software decoder for RTSP" >&2
                fi
                ;;
            *)
                base_pipeline+="avdec_h264 max-threads=4 ! videoconvert ! "
                echo "Using software decoder for RTSP" >&2
                ;;
        esac
        
    elif [[ "$video_path" == http://* ]] || [[ "$video_path" == https://* ]]; then
        echo "Setting up HTTP source for: $video_path" >&2
        base_pipeline="souphttpsrc location=\"$video_path\" ! decodebin ! videoconvert ! "
        
    else
        echo "Setting up file source for: $video_path" >&2
        if [[ ! -f "$video_path" ]]; then
            echo "Error: Video file not found: $video_path" >&2
            exit 1
        fi
        base_pipeline="filesrc location=\"$video_path\" ! decodebin ! videoconvert ! "
    fi
    
    echo "$base_pipeline"
}

# Function to build inference pipeline with device selection
build_inference_pipeline() {
    local source_pipeline="$1"
    local camera_id="$2"
    local video_path="$3"
    local device="$4"
    local pipeline=""
    
    # Create tags for Kafka messages
    local detect_tag="{\\\"camera\\\": \\\"$camera_id\\\", \\\"video\\\": \\\"$video_path\\\", \\\"task\\\": \\\"gvadetect\\\", \\\"device\\\": \\\"$device\\\"}"
    local pose_tag="{\\\"camera\\\": \\\"$camera_id\\\", \\\"video\\\": \\\"$video_path\\\", \\\"task\\\": \\\"gvapose\\\", \\\"device\\\": \\\"$device\\\"}"
    
    if $RUN_DETECT && $RUN_POSE; then
        echo "Building combined detection and pose pipeline for $camera_id (Device: $device)" >&2
        
        # Combined pipeline with tee for branching
        pipeline="$source_pipeline tee name=t_$camera_id "
        
        # Detection branch
        pipeline+="t_$camera_id. ! queue max-size-buffers=10 leaky=downstream ! "
        pipeline+="gvadetect model=\"$DETECT_MODEL\" device=\"$device\" pre-process-backend=ie ! "
        pipeline+="gvametaconvert add-tensor-data=true tags=\"$detect_tag\" ! "
        pipeline+="gvametapublish file-format=json-lines method=kafka address=\"$KAFKA_BROKER\" topic=\"$KAFKA_TOPIC\" ! "
        pipeline+="fakesink sync=false "
        
        # Pose branch
        pipeline+="t_$camera_id. ! queue max-size-buffers=10 leaky=downstream ! "
        pipeline+="gvadetect model=\"$POSE_MODEL\" device=\"$device\" pre-process-backend=opencv ! "
        pipeline+="gvametaconvert format=json tags=\"$pose_tag\" ! "
        pipeline+="gvametapublish file-format=json-lines method=kafka address=\"$KAFKA_BROKER\" topic=\"$KAFKA_TOPIC\" ! "
        pipeline+="fakesink sync=false "
        
    elif $RUN_DETECT; then
        echo "Building detection-only pipeline for $camera_id (Device: $device)" >&2
        
        pipeline="$source_pipeline "
        pipeline+="gvadetect model=\"$DETECT_MODEL\" device=\"$device\" pre-process-backend=ie ! "
        pipeline+="gvametaconvert add-tensor-data=true tags=\"$detect_tag\" ! "
        pipeline+="gvametapublish file-format=json-lines method=kafka address=\"$KAFKA_BROKER\" topic=\"$KAFKA_TOPIC\" ! "
        pipeline+="fakesink sync=false "
        
    elif $RUN_POSE; then
        echo "Building pose-only pipeline for $camera_id (Device: $device)" >&2
        
        pipeline="$source_pipeline "
        pipeline+="gvadetect model=\"$POSE_MODEL\" device=\"$device\" pre-process-backend=opencv ! "
        pipeline+="gvametaconvert format=json tags=\"$pose_tag\" ! "
        pipeline+="gvametapublish file-format=json-lines method=kafka address=\"$KAFKA_BROKER\" topic=\"$KAFKA_TOPIC\" ! "
        pipeline+="fakesink sync=false "
    fi
    
    echo "$pipeline"
}

# Main execution
echo "=== DLStreamer Video Processing Started ==="
echo "Videos: ${VIDEO_LIST[*]}"
echo "Tasks: ${TASK_LIST[*]}"
echo "Camera IDs: ${CAMERA_LIST[*]}"
echo "Requested Device: $DEVICE"
echo "Kafka Broker: $KAFKA_BROKER"
echo "Kafka Topic: $KAFKA_TOPIC"

# Select optimal device
SELECTED_DEVICE=$(select_device "$DEVICE")
echo "Selected Device: $SELECTED_DEVICE"

# Send start boundary messages to Kafka
echo "Sending start boundary messages to Kafka..."
for i in "${!VIDEO_LIST[@]}"; do
    VIDEO_PATH="${VIDEO_LIST[$i]}"
    CAM_ID="${CAMERA_LIST[$i]}"
    
    if $RUN_DETECT; then
        python3 ./scripts/define_video_boundary_kafka.py \
            --video "$VIDEO_PATH" \
            --task "gvadetect" \
            --status "start" \
            --camera "$CAM_ID" \
            --kafka-broker "$KAFKA_BROKER" \
            --kafka-topic "$KAFKA_TOPIC" || echo "Warning: Could not send detect start boundary for $CAM_ID"
    fi
    
    if $RUN_POSE; then
        python3 ./scripts/define_video_boundary_kafka.py \
            --video "$VIDEO_PATH" \
            --task "gvapose" \
            --status "start" \
            --camera "$CAM_ID" \
            --kafka-broker "$KAFKA_BROKER" \
            --kafka-topic "$KAFKA_TOPIC" || echo "Warning: Could not send pose start boundary for $CAM_ID"
    fi
done

# Build and execute pipelines
if [[ ${#VIDEO_LIST[@]} -eq 1 ]]; then
    # Single video processing
    VIDEO_PATH="${VIDEO_LIST[0]}"
    CAM_ID="${CAMERA_LIST[0]}"
    
    echo "Processing single video: $VIDEO_PATH (Camera: $CAM_ID, Device: $SELECTED_DEVICE)"
    
    SOURCE_PIPELINE=$(optimize_source_pipeline "$VIDEO_PATH" "$SELECTED_DEVICE")
    FULL_PIPELINE=$(build_inference_pipeline "$SOURCE_PIPELINE" "$CAM_ID" "$VIDEO_PATH" "$SELECTED_DEVICE")
    
    echo "Executing pipeline..."
    echo "Pipeline: $FULL_PIPELINE" >&2
    
    gst-launch-1.0 $FULL_PIPELINE
    
else
    # Multiple video processing - create parallel pipelines
    echo "Processing multiple videos in parallel..."
    
    PIDS=()
    
    for i in "${!VIDEO_LIST[@]}"; do
        VIDEO_PATH="${VIDEO_LIST[$i]}"
        CAM_ID="${CAMERA_LIST[$i]}"
        
        echo "Starting pipeline for: $VIDEO_PATH (Camera: $CAM_ID, Device: $SELECTED_DEVICE)"
        
        SOURCE_PIPELINE=$(optimize_source_pipeline "$VIDEO_PATH" "$SELECTED_DEVICE")
        FULL_PIPELINE=$(build_inference_pipeline "$SOURCE_PIPELINE" "$CAM_ID" "$VIDEO_PATH" "$SELECTED_DEVICE")
        
        echo "Pipeline $i: $FULL_PIPELINE" >&2
        
        # Run each pipeline in background
        (
            echo "Starting inference for camera $CAM_ID..."
            gst-launch-1.0 $FULL_PIPELINE
        ) &
        
        PIDS+=($!)
        
        # Small delay between starting pipelines to avoid resource contention
        sleep 2
    done
    
    echo "All pipelines started. PIDs: ${PIDS[*]}"
    echo "Waiting for pipelines to complete..."
    
    # Wait for all background processes
    for pid in "${PIDS[@]}"; do
        wait $pid
        echo "Pipeline with PID $pid completed"
    done
fi

# Send end boundary messages to Kafka
echo "Sending end boundary messages to Kafka..."
for i in "${!VIDEO_LIST[@]}"; do
    VIDEO_PATH="${VIDEO_LIST[$i]}"
    CAM_ID="${CAMERA_LIST[$i]}"
    
    if $RUN_DETECT; then
        python3 ./scripts/define_video_boundary_kafka.py \
            --video "$VIDEO_PATH" \
            --task "gvadetect" \
            --status "end" \
            --camera "$CAM_ID" \
            --kafka-broker "$KAFKA_BROKER" \
            --kafka-topic "$KAFKA_TOPIC" || echo "Warning: Could not send detect end boundary for $CAM_ID"
    fi
    
    if $RUN_POSE; then
        python3 ./scripts/define_video_boundary_kafka.py \
            --video "$VIDEO_PATH" \
            --task "gvapose" \
            --status "end" \
            --camera "$CAM_ID" \
            --kafka-broker "$KAFKA_BROKER" \
            --kafka-topic "$KAFKA_TOPIC" || echo "Warning: Could not send pose end boundary for $CAM_ID"
    fi
done

echo "=== DLStreamer Video Processing Completed ==="

