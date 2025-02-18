import os
import json
import subprocess
from behave import given, when, then

MODEL = "yolo11s"
DEVICE = "CPU"
INPUT_VIDEO = "/videos/person-bicycle-car-detection.mp4"
OUTPUT_TYPE = "json"
OUTPUT_JSON_PATH = "/mnt/data/output.json"
YOLO_SCRIPT_PATH = "/home/dlstreamer/samples/gstreamer/gst_launch/detection_with_yolo/yolo_detect.sh"

@given("the DL Streamer pipeline is running")
def step_impl_pipeline_running(context):
    """
    Verify that the DL Streamer process is running inside the container.
    """
    result = subprocess.run(
        ["pgrep", "-x", "bash"],  # Check if any bash process is running
        capture_output=True,
        text=True,
        check=False
    )
    assert result.returncode == 0, "DL Streamer process is not running!"

@when("I submit a sample video for detection")
def step_impl_submit_video(context):
    """
    Run object detection inside the DL Streamer container.
    """
    command = [
        YOLO_SCRIPT_PATH, MODEL, DEVICE, INPUT_VIDEO, OUTPUT_TYPE
    ]
    context.process = subprocess.run(
        command,
        capture_output=True,
        text=True
    )

    if context.process.returncode != 0:
        print("Error running detection:", context.process.stderr)

@then("I should receive an object detection result")
def step_impl_verify_detection(context):
    """
    Validate the detection results.
    """
    assert context.process.returncode == 0, (
        f"Detection command failed with error: {context.process.stderr}"
    )

    # Read JSON output from the mounted volume
    try:
        with open(OUTPUT_JSON_PATH, "r") as json_file:
            detection_result = json.load(json_file)
    except json.JSONDecodeError as e:
        assert False, f"Output is not valid JSON: {e}"
    except FileNotFoundError:
        assert False, "Output JSON file not found!"

    assert detection_result, "Detection JSON output is empty"

    print("Object detection completed successfully with JSON output:", detection_result)
