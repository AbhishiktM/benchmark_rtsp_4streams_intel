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
