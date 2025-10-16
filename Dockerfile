FROM intel/dlstreamer:latest
USER root
SHELL ["/bin/bash", "-c"]
# Set working directory
WORKDIR /home/dlstreamer
# Install required system packages
RUN apt-get update && \
    DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
        apt-utils \
        pciutils \
        netcat-openbsd \
        procps \
        wget \
        curl \
        python3-pip \
        python3-dev || true && \
    apt-get install -y --no-install-recommends \
        gstreamer1.0-plugins-base \
        gstreamer1.0-plugins-good \
        gstreamer1.0-plugins-bad \
        gstreamer1.0-plugins-ugly \
        gstreamer1.0-libav || true && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*
# Install Python packages
RUN python3 -m pip install --upgrade --ignore-installed pip setuptools wheel --break-system-packages && \
    pip3 install --no-cache-dir \
        confluent-kafka==2.3.0 \
        numpy==1.26.4 \
        psutil==5.9.5 \
        docker==6.1.3 \
        --break-system-packages
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
ENV LD_LIBRARY_PATH=/usr/lib/x86_64-linux-gnu:/opt/intel/openvino/runtime/lib/intel64
CMD ["/bin/bash"]














