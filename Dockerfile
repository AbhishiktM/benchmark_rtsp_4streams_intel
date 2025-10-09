# # FROM intel/dlstreamer:latest

# # USER root

# # WORKDIR /home/dlstreamer

# # # Update package lists and install Python pip
# # RUN apt-get update && \
# #     apt-get install -y python3-pip python3-dev && \
# #     apt-get clean && \
# #     rm -rf /var/lib/apt/lists/*

# # # Install Python packages directly (skip pip upgrade)
# # RUN python3 -m pip install kafka-python numpy psutil docker --break-system-packages

# # # Create necessary directories
# # RUN mkdir -p /home/dlstreamer/scripts && \
# #     mkdir -p /home/dlstreamer/models && \
# #     mkdir -p /home/dlstreamer/videos && \
# #     mkdir -p /benchmark_results

# # # Set permissions
# # RUN chown -R dlstreamer:dlstreamer /home/dlstreamer && \
# #     chown -R dlstreamer:dlstreamer /benchmark_results

# # # Switch back to dlstreamer user
# # USER dlstreamer

# # # Make scripts executable (will be mounted as volumes)
# # VOLUME ["/home/dlstreamer/scripts", "/home/dlstreamer/models", "/home/dlstreamer/videos"]

# # # Default command - will be overridden by docker-compose
# # CMD ["bash"]

# FROM intel/dlstreamer:latest

# USER root

# WORKDIR /home/dlstreamer

# # Update package lists and install dependencies
# RUN apt-get update && \
#     apt-get install -y \
#     python3-pip \
#     python3-dev \
#     wget \
#     gnupg2 \
#     software-properties-common \
#     && apt-get clean && \
#     rm -rf /var/lib/apt/lists/*

# # Install NVIDIA Container Toolkit repository
# RUN distribution=$(. /etc/os-release;echo $ID$VERSION_ID) && \
#     curl -s -L https://nvidia.github.io/nvidia-docker/gpgkey | apt-key add - && \
#     curl -s -L https://nvidia.github.io/nvidia-docker/$distribution/nvidia-docker.list | tee /etc/apt/sources.list.d/nvidia-docker.list

# # Install NVIDIA drivers and CUDA support (if available)
# RUN apt-get update && \
#     apt-get install -y \
#     nvidia-driver-470 \
#     nvidia-cuda-toolkit \
#     || echo "NVIDIA drivers not available - CPU only mode"

# # Install Python packages
# RUN python3 -m pip install kafka-python numpy psutil docker --break-system-packages

# # Install GStreamer NVIDIA plugins
# RUN apt-get update && \
#     apt-get install -y \
#     gstreamer1.0-plugins-bad \
#     gstreamer1.0-vaapi \
#     || echo "Additional GStreamer plugins not available"

# # Create necessary directories
# RUN mkdir -p /home/dlstreamer/scripts && \
#     mkdir -p /home/dlstreamer/models && \
#     mkdir -p /home/dlstreamer/videos && \
#     mkdir -p /benchmark_results

# # Set permissions
# RUN chown -R dlstreamer:dlstreamer /home/dlstreamer && \
#     chown -R dlstreamer:dlstreamer /benchmark_results

# # Switch back to dlstreamer user
# USER dlstreamer

# VOLUME ["/home/dlstreamer/scripts", "/home/dlstreamer/models", "/home/dlstreamer/videos"]

# CMD ["bash"]

FROM intel/dlstreamer:latest

USER root

WORKDIR /home/dlstreamer

# Update package lists and install ALL necessary dependencies
RUN apt-get update && \
    apt-get install -y \
    python3-pip \
    python3-dev \
    wget \
    curl \
    gnupg2 \
    software-properties-common \
    vainfo \
    intel-media-va-driver \
    mesa-va-drivers \
    i965-va-driver \
    netcat-openbsd \
    procps \
    && apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Install Python packages
RUN python3 -m pip install kafka-python numpy psutil docker --break-system-packages

# Install ALL GStreamer plugins for maximum compatibility
RUN apt-get update && \
    apt-get install -y \
    gstreamer1.0-plugins-bad \
    gstreamer1.0-vaapi \
    gstreamer1.0-plugins-ugly \
    gstreamer1.0-libav \
    gstreamer1.0-plugins-good \
    && apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Create necessary directories
RUN mkdir -p /home/dlstreamer/scripts && \
    mkdir -p /home/dlstreamer/models && \
    mkdir -p /home/dlstreamer/videos && \
    mkdir -p /benchmark_results

# Set permissions
RUN chown -R dlstreamer:dlstreamer /home/dlstreamer && \
    chown -R dlstreamer:dlstreamer /benchmark_results

# Switch back to dlstreamer user
USER dlstreamer

VOLUME ["/home/dlstreamer/scripts", "/home/dlstreamer/models", "/home/dlstreamer/videos"]

CMD ["bash"]
