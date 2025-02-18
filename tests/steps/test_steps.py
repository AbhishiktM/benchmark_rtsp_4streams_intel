import json
import subprocess
import os
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
    Automatically pass since we are inside the container.
    """
    print("DL Streamer is running inside the container, automatically passing this step.")
    pass  # No need to check anything.

@when("I submit a sample video for detection")
def step_impl_submit_video(context):
    """
    Run object detection inside the DL Streamer container.
    """

    # Debug: Print actual file locations
    print("\n🔎 Searching for files in container...")

    # Search for YOLO script
    print("\n📂 Listing files in /home/dlstreamer/samples/gstreamer/")
    subprocess.run(["ls", "-R", "/home/dlstreamer/samples/gstreamer/"], check=False)

    # Search for input video
    print("\n📂 Listing files in /videos/")
    subprocess.run(["ls", "-R", "/videos/"], check=False)

    # Search for output folder
    print("\n📂 Listing files in /mnt/data/")
    subprocess.run(["ls", "-R", "/mnt/data/"], check=False)

    # Ensure script exists before running
    assert os.path.exists(YOLO_SCRIPT_PATH), f"🚨 YOLO script not found at {YOLO_SCRIPT_PATH}"
    assert os.path.exists(INPUT_VIDEO), f"🚨 Input video not found at {INPUT_VIDEO}"

    command = [
        YOLO_SCRIPT_PATH, MODEL, DEVICE, INPUT_VIDEO, OUTPUT_TYPE
    ]
    context.process = subprocess.run(
        command,
        capture_output=True,
        text=True
    )

    if context.process.returncode != 0:
        print("❌ Error running detection:", context.process.stderr)

@then("I should receive an object detection result")
def step_impl_verify_detection(context):
    """
    Validate the detection results.
    """
    assert context.process.returncode == 0, (
        f"❌ Detection command failed with error: {context.process.stderr}"
    )

    # Debug: Print actual file paths
    print("\n🔎 Checking if output JSON exists:")
    subprocess.run(["ls", "-lh", OUTPUT_JSON_PATH], check=False)

    assert os.path.exists(OUTPUT_JSON_PATH), f"🚨 Output JSON file not found at {OUTPUT_JSON_PATH}"

    # Read JSON output from the mounted volume
    try:
        with open(OUTPUT_JSON_PATH, "r") as json_file:
            detection_result = json.load(json_file)
    except json.JSONDecodeError as e:
        assert False, f"🚨 Output is not valid JSON: {e}"
    except FileNotFoundError:
        assert False, "🚨 Output JSON file not found!"

    assert detection_result, "🚨 Detection JSON output is empty"

    print("\n✅ Object detection completed successfully with JSON output:", detection_result)
