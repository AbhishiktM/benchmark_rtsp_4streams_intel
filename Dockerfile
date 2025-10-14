FROM intel/dlstreamer:latest

USER root

WORKDIR /home/dlstreamer

# Install only essential packages
RUN apt-get update && apt-get install -y \
    # Utilities
    pciutils \
    python3-pip \
    netcat-openbsd \
    procps \
    wget \
    curl \
    # Additional GStreamer plugins
    gstreamer1.0-plugins-ugly \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Install Python packages
RUN python3 -m pip install --no-cache-dir \
    kafka-python \
    numpy \
    psutil \
    docker \
    --break-system-packages

# Create directories
RUN mkdir -p \
    /home/dlstreamer/scripts \
    /home/dlstreamer/models \
    /home/dlstreamer/videos \
    /benchmark_results

# Set permissions
RUN chown -R dlstreamer:dlstreamer /home/dlstreamer && \
    chown -R dlstreamer:dlstreamer /benchmark_results

USER dlstreamer

VOLUME ["/home/dlstreamer/scripts", "/home/dlstreamer/models", "/home/dlstreamer/videos"]

CMD ["bash"]
