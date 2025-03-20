FROM intel/dlstreamer:latest

WORKDIR /home/dlstreamer

COPY scripts /home/dlstreamer/scripts
COPY models /home/dlstreamer/models
COPY videos /home/dlstreamer/videos

RUN pip3 install kafka-python opencv-python ultralytics numpy

CMD ["python3", "/home/dlstreamer/scripts/dlstreamer_consumer.py"]
