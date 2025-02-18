import json
import subprocess
import os
from behave import given, when, then

MODEL = "yolo11s"
DEVICE = "CPU"
INPUT_VIDEO = "/videos/person-bicycle-car-detection.mp4"
OUTPUT_TYPE = "json"
OUTPUT_JSON_PATH = "/mnt/data/output.json"
YOLO_SCRIPT_PATH = None  # Will be detected dynamically

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

    # Search for `yolo_detect.sh` dynamically
    print("\n🔎 Searching for `yolo_detect.sh` inside the container...")
    result = subprocess.run(["find", "/", "-name", "yolo_detect.sh", "2>/dev/null"], capture_output=True, text=True)

    global YOLO_SCRIPT_PATH
    YOLO_SCRIPT_PATH = result.stdout.strip()  # Get the first found path

    if not YOLO_SCRIPT_PATH:
        print("🚨 `yolo_detect.sh` not found in the container!")
        subprocess.run(["find", "/", "-name", "yolo_detect.sh"], check=False)  # Debug: Full search output
        assert False, "🚨 YOLO script is missing. Please check the container!"

    print(f"✅ Found YOLO script at: {YOLO_SCRIPT_PATH}")

    # Debug: Print file locations
    print("\n🔎 Checking essential paths inside container:")
    
    for path in [YOLO_SCRIPT_PATH, INPUT_VIDEO, OUTPUT_JSON_PATH]:
        exists = os.path.exists(path)
        print(f"Path: {path} | Exists: {exists}")

    # Ensure script and input video exist before running
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
