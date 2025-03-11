FROM intel/dlstreamer:latest

WORKDIR /home/dlstreamer

COPY scripts /home/dlstreamer/scripts
COPY models /home/dlstreamer/models
COPY videos /home/dlstreamer/videos

RUN pip3 install kafka-python

CMD ["python3", "/home/dlstreamer/scripts/dlstreamer_consumer.py"]
