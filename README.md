# DLStreamer Quick Setup (Intel Arc GPU + Linux)

## 1. Install Requirements
```bash
sudo apt-get update
sudo apt-get install -y docker.io docker-compose make git intel-opencl-icd intel-level-zero-gpu level-zero intel-media-va-driver-non-free vainfo clinfo intel-media-va-driver libmfx1 libmfxgen1 libvpl2
```

## 2. Verify GPU
```bash
lspci | grep -i vga
ls -la /dev/dri/
clinfo | grep "Intel"
vainfo | grep "iHD"
```

## 3. Clone Repo
```bash
git clone <your-repo-url>
cd intel-dlstreamer-service
```

## 4. Setup & Run
```bash
make setup
```

## 5. Verify GPU is Used
```bash
docker logs dlstreamer_auto | head -30
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



## Commands Reference

```bash
make setup          # Initial setup
make start          # Start services
make stop           # Stop services
make restart        # Restart services
make clean          # Remove everything
make logs           # DLStreamer logs
make logs-streams   # RTSP stream logs
make gpu-monitor    # Monitor GPU
make test-streams   # Test RTSP availability
