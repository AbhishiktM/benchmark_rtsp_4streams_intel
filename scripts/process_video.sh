#!/bin/bash
VIDEO_PATH=$1
PROCESSING=$2
MODEL_PATH=$3

echo "Processing video: $VIDEO_PATH with tasks: $PROCESSING"

PIPELINE="gst-launch-1.0 filesrc location=$VIDEO_PATH ! decodebin !"

PROCESSING=$(echo "$PROCESSING" | tr -d '[]"')
PROCESSING=$(echo "$PROCESSING" | sed "s/,/ /g" | tr -d "'")
echo "DEBUG: PROCESSING=\"$PROCESSING\""

for task in $PROCESSING; do
    echo "DEBUG: Task = \"$task\""
    if [[ "$task" == "gvadetect" ]]; then
        PIPELINE+=" gvadetect model=$MODEL_PATH device=CPU pre-process-backend=ie ! queue !"
    elif [[ "$task" == "gvatrack" ]]; then
        PIPELINE+=" gvatrack tracking-type=short-term-imageless ! queue !"
    elif [[ "$task" == "gvaclassify" ]]; then
        PIPELINE+=" gvaclassify model=$MODEL_PATH device=CPU ! queue !"
    fi
done

PIPELINE+=" gvametaconvert add-tensor-data=true ! gvametapublish file-format=json-lines method=kafka address=kafka:9092 topic=dlstreamer_output ! fakesink async=false"

echo "Running Pipeline: $PIPELINE"
eval "$PIPELINE"
