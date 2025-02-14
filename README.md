# Intel DLStreamer Service - Setup and Usage Guide

## Overview
This document provides installation and setup instructions for running Intel DLStreamer in **MacOS**, **Ubuntu 22.04**, and **Ubuntu 24.04** using Docker containers. It also includes codec conversion steps and running inference with GStreamer pipelines.

---

## 1. Setup Instructions

### MacOS
#### **Prerequisites**
Install **XQuartz** for X11 forwarding:
```sh
brew install xquartz
```

Start XQuartz:
```sh
open -a XQuartz
xhost + 127.0.0.1
xhost +local:
```

Run the **DLStreamer** container:
```sh
podman run -it  -v $HOME/.Xauthority:/root/.Xauthority:rw   \
  -e DISPLAY=$DISPLAY   \
  -v /Users/kushal/intel/models:/home/dlstreamer/models    \
  -v /Users/kushal/intel/videos:/home/dlstreamer/videos   \
  --env MODELS_PATH=/home/dlstreamer/models   \
  --user root    intel/dlstreamer:2024.1.2-ubuntu22 bash
```

#### **Install Dependencies inside the Container**
```sh
apt install -y libxtst6 libxv1
apt-get install python3-pip
python3 -m pip install openvino-dev[onnx,tensorflow,pytorch]
```

---

### Ubuntu 22.04 & Ubuntu 24.04
#### **Prerequisites**
Install Docker if not already installed:
```sh
sudo apt update
sudo apt install -y docker.io
```

Ensure Docker is running:
```sh
sudo systemctl start docker
sudo systemctl enable docker
```

Grant permission to run Docker as a non-root user:
```sh
sudo usermod -aG docker $USER
newgrp docker
```

#### **Run DLStreamer Container**
For **Ubuntu 22.04**:
```sh
docker run -it --rm \
  -v ~/intel/models:/home/dlstreamer/models \
  -v ~/intel/videos:/home/dlstreamer/videos \
  --env MODELS_PATH=/home/dlstreamer/models \
  --user root intel/dlstreamer:2024.1.2-ubuntu22 bash
```

For **Ubuntu 24.04 (Latest Version)**:
```sh
podman run -it  -v $HOME/.Xauthority:/root/.Xauthority:rw   \
  -e DISPLAY=$DISPLAY   \
  -v /Users/kushal/intel/models:/home/dlstreamer/models    \
  -v /Users/kushal/intel/videos:/home/dlstreamer/videos   \
  --env MODELS_PATH=/home/dlstreamer/models   \
  --user root    intel/dlstreamer:latest bash
```

#### **Install Dependencies inside the Container**
```sh
apt update && apt install -y libxtst6 libxv1
apt-get install python3-pip
python3 -m pip install openvino-dev[onnx,tensorflow,pytorch]
```

---

## 2. Handling Codec Issues
If you encounter codec compatibility issues, use **FFmpeg** to convert video formats.

Install FFmpeg on Ubuntu:
```sh
sudo apt install -y ffmpeg
```

Convert videos:
```sh
ffmpeg -i ~/intel/videos/arducam_test1.mp4 -t 5 -c copy ~/intel/videos/ardu1_trimmed.mp4

ffmpeg -i ~/intel/videos/ardu1_trimmed.mp4 -vf "scale=1920:1080" -c:v libx264 -profile:v high -pix_fmt yuv420p -b:v 5353k -r 30 -c:a aac -b:a 128k -ar 44100 -strict experimental ~/intel/videos/arducam_test1_converted.mp4
```

---

## 3. Running Inference with GStreamer

### **Object Detection and Output to JSON**
```sh
gst-launch-1.0 filesrc location=/home/dlstreamer/videos/brio_rec.mp4 ! decodebin ! \
  gvadetect model=/home/dlstreamer/models/intel/custom-model/best.xml device=CPU ! queue ! \
  gvawatermark ! gvametaconvert format=json ! gvametapublish method=file file-path=/home/dlstreamer/output1.json ! fakesink
```

### **Processing RTSP Stream**
```sh
gst-launch-1.0 \
  urisourcebin uri=rtsp://192.168.29.107:8554/mystream ! decodebin ! \
  gvadetect model=/home/dlstreamer/models/intel/custom-model/best.xml device=CPU ! queue ! \
  gvawatermark ! gvametaconvert format=json ! gvametapublish method=file file-path=/home/dlstreamer/output_rtsp.json ! fakesink
```
### **Alternative Detection Method Using YOLO Models**

Instead of using the standard detection method with `gvadetect`, you can utilize **YOLO models** for object detection within DLStreamer. The following script executes YOLO-based detection on a given video file and outputs the results in JSON format.

#### **Running YOLO Detection**
To run YOLO-based detection inside the container, use the following command:
```sh
/home/dlstreamer/dlstreamer/samples/gstreamer/gst_launch/detection_with_yolo# ./yolo_detect.sh "yolo11s" "CPU" "/home/dlstreamer/videos/brio_rec.mp4" "json"
```
#### **Parameters Explained:**
- `"yolo11s"` → Specifies the YOLO model variant (modify as per your available models).
- `"CPU"` → Defines the processing device (use `"GPU"` if you have hardware acceleration available).
- `"/home/dlstreamer/videos/brio_rec.mp4"` → Path to the input video file.
- `"json"` → Output format of the detection results.

#### **Expected Output:**
- The detection results will be stored in JSON format, containing bounding box coordinates, confidence scores, and detected classes.

This method is useful when leveraging YOLO models instead of the default OpenVINO-based detection pipelines in DLStreamer.
---

### **Converting Yolo models to OpenVino format and process the output video**

- Model Conversion Scripts - [Scripts](./model_conversion_scripts/)
- Output Video Script - [Scripts](./video_bb_overlay_scripts/)
