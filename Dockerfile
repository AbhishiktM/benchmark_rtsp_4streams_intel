FROM intel/dlstreamer:latest

# Set working directory
WORKDIR /home/dlstreamer

# Install required system packages
RUN apt-get update && apt-get install -y \
    pciutils \
    netcat-openbsd \
    procps \
    wget \
    curl \
    python3-pip \
    python3-dev \
    gstreamer1.0-plugins-ugly \
    gstreamer1.0-libav \
    && rm -rf /var/lib/apt/lists/*

# Install Python packages
RUN pip3 install --no-cache-dir \
    kafka-python==2.0.2 \
    numpy==1.24.3 \
    psutil==5.9.5 \
    docker==6.1.3

# Create necessary directories
RUN mkdir -p /home/dlstreamer/scripts \
    /home/dlstreamer/models \
    /home/dlstreamer/videos \
    /benchmark_results

# Set proper permissions
RUN chown -R dlstreamer:dlstreamer /home/dlstreamer /benchmark_results

# Switch to dlstreamer user
USER dlstreamer

# Set environment variables for Arc A770
ENV LIBVA_DEVICE=/dev/dri/renderD129
ENV GST_VAAPI_DRM_DEVICE=/dev/dri/renderD129
ENV LIBVA_DRIVER_NAME=iHD
ENV GPU_DEVICE_ORDINAL=1

CMD ["/bin/bash"]
