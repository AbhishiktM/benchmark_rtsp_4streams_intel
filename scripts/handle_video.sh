#!/bin/bash
SOURCE_FILE=$1
DEST_DIR="/home/dlstreamer/videos"

echo "Moving $SOURCE_FILE to DLStreamer processing directory..."
mv "$SOURCE_FILE" "$DEST_DIR/"
