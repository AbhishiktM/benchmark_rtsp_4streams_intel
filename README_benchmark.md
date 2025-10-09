# 🧠 Universal DLStreamer AI Inference Pipeline

A comprehensive AI inference pipeline using **Intel DLStreamer** with automatic hardware detection for **Intel**, **AMD**, and **NVIDIA** systems.

## 🚀 Quick Start (Any Linux System)

### 🧩 Prerequisites
- Docker and Docker Compose installed  
- Linux system with GPU drivers (optional but recommended)

### ⚡ One-Command Setup

```bash
# Clone repository
git clone <your-repo-url>
cd intel-dlstreamer-service

# Create network and start everything
make setup
```

If you prefer manual control over each step, follow the manual setup below.

### 🧱 Manual Setup

```bash
# 1. Create Docker network
docker network create dlstreamer_shared_net

# 2. Start RTSP streams
docker compose -f docker-compose.streams.yml up -d

# 3. Start auto-detection pipeline
docker compose -f docker-compose.dlstreamer.yml --profile auto up -d

# 4. Monitor performance
docker logs -f benchmark_monitor
```

### 📊 Monitoring Results

To check performance and system behavior in real-time:

```bash
# Real-time performance monitoring
docker logs -f benchmark_monitor

# Check benchmark files
ls -la benchmark_results/

# View system detection info
docker logs dlstreamer_auto | head -20
```

## 🔧 Hardware Support

| Hardware Type | Detection | Mode |
|----------------|------------|------|
| **Intel Systems** | Auto-detects Intel GPU | GPU acceleration |
| **AMD Systems** | Auto-detects AMD GPU | Hybrid mode (GPU decode + CPU inference) |
| **NVIDIA Systems** | Auto-detects NVIDIA GPU | Hybrid mode |
| **CPU-only Systems** | Automatic fallback | CPU processing |

## 📁 Project Structure

```
├── Dockerfile                     # Universal container definition
├── docker-compose.dlstreamer.yml  # Main pipeline configuration
├── docker-compose.streams.yml     # RTSP stream server
├── benchmark_monitor.py           # Performance monitoring
├── scripts/                       # Processing scripts
├── models/                        # AI models (OpenVINO format)
├── videos/                        # Sample video files
└── README.md                      # This file
```

## 🛠️ Troubleshooting

### ⚙️ GPU Not Detected

```bash
# Check GPU drivers
nvidia-smi   # For NVIDIA
vainfo       # For Intel/AMD
```

### 🐢 Performance Issues

```bash
# Check system resources
docker stats
htop
```

### 🧩 Container Issues

```bash
# Restart services
docker compose down
docker compose --profile auto up -d
```

## 📈 Expected Performance

| Hardware | Expected FPS per Camera | Efficiency |
|-----------|-------------------------|-------------|
| Intel GPU | 20–30 FPS | 70–90% |
| NVIDIA GPU (Hybrid) | 15–25 FPS | 50–80% |
| AMD GPU (Hybrid) | 10–20 FPS | 40–70% |
| CPU Only | 2–8 FPS | 10–30% |

## 🔄 Different Modes

```bash
# Auto-detection (recommended)
docker compose --profile auto up -d

# CPU-only mode
docker compose --profile cpu up -d

# Force hybrid mode (GPU decode + CPU inference)
docker compose --profile hybrid up -d
```

## 📦 Benchmark Results

Benchmark logs and performance metrics are automatically saved in:

```
benchmark_results/
```

You can export them as `.csv` for further analysis.

## 🤝 Contributing

Contributions are welcome!  
If you find bugs or performance issues, feel free to open an issue or submit a PR.

## 🧠 Credits

Developed as a universal DLStreamer-based AI inference pipeline with a focus on cross-GPU support (Intel, AMD, NVIDIA) and real-time benchmarking.

⭐ **If you find this useful, give it a star on GitHub!**