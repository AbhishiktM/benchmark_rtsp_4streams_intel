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
    Verify that the DL Streamer container is running.
    """
    result = subprocess.run(
        ["docker", "inspect", "-f", "{{.State.Running}}", "dlstreamer"],
        capture_output=True,
        text=True,
        check=False
    )
    running_status = result.stdout.strip().lower()
    assert running_status == "true", "DL Streamer container is not running"

@when("I submit a sample video for detection")
def step_impl_submit_video(context):
    """
    Run object detection inside the DL Streamer container.
    """
    command = [
        "docker", "exec", "dlstreamer", "bash", "-c",
        f"{YOLO_SCRIPT_PATH} {MODEL} {DEVICE} {INPUT_VIDEO} {OUTPUT_TYPE} > {OUTPUT_JSON_PATH}"
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

    # Read JSON output from the container
    json_command = [
        "docker", "exec", "dlstreamer", "bash", "-c",
        f"cat {OUTPUT_JSON_PATH}"
    ]
    json_process = subprocess.run(
        json_command,
        capture_output=True,
        text=True
    )

    if json_process.returncode != 0:
        assert False, f"Failed to read JSON output: {json_process.stderr}"

    try:
        detection_result = json.loads(json_process.stdout)
    except json.JSONDecodeError as e:
        assert False, f"Output is not valid JSON: {e}"

    assert detection_result, "Detection JSON output is empty"

    print("Object detection completed successfully with JSON output:", detection_result)
