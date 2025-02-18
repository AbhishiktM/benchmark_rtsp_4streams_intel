import json
import subprocess
import os
import time
from behave import given, when, then

MODEL = "yolo11s"
DEVICE = "CPU"
INPUT_VIDEO = "/videos/person-bicycle-car-detection.mp4"
OUTPUT_TYPE = "json"
OUTPUT_JSON_PATH = "/mnt/data/output.json"
YOLO_SCRIPT_PATH = "/opt/intel/dlstreamer/samples/gstreamer/gst_launch/detection_with_yolo/yolo_detect.sh"  
MODEL_PATH_ENV = None  # This will be assigned dynamically

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
    Run object detection inside the DL Streamer container and wait for completion.
    """

    # Step 1: Find the Models Folder
    print("\n🔎 Searching for `models` directory inside the container...")
    result = subprocess.run(["find", "/", "-type", "d", "-name", "models", "2>/dev/null"], capture_output=True, text=True)

    global MODEL_PATH_ENV
    MODEL_PATH_ENV = result.stdout.strip()  # Get the first found path

    if not MODEL_PATH_ENV:
        print("🚨 `models` directory not found in the container!")
        subprocess.run(["find", "/", "-type", "d", "-name", "models"], check=False)  # Debug: Full search output
        assert False, "🚨 Models folder is missing. Please check the container!"

    print(f"✅ Found Models folder at: {MODEL_PATH_ENV}")
    os.environ["MODEL_PATH"] = MODEL_PATH_ENV  # Assign to environment variable

    # Debug: Print actual file locations
    print("\n🔎 Checking essential paths inside container:")
    
    for path in [YOLO_SCRIPT_PATH, INPUT_VIDEO, OUTPUT_JSON_PATH, MODEL_PATH_ENV]:
        exists = os.path.exists(path)
        print(f"Path: {path} | Exists: {exists}")

    # Ensure script and input video exist before running
    assert os.path.exists(YOLO_SCRIPT_PATH), f"🚨 YOLO script not found at {YOLO_SCRIPT_PATH}"
    assert os.path.exists(INPUT_VIDEO), f"🚨 Input video not found at {INPUT_VIDEO}"

    command = [
        YOLO_SCRIPT_PATH, MODEL, DEVICE, INPUT_VIDEO, OUTPUT_TYPE
    ]

    print("\n🚀 Starting YOLO detection... Waiting for it to complete.")
    
    process = subprocess.Popen(
        command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, env=os.environ
    )

    # Print YOLO script output in real-time
    while True:
        output = process.stdout.readline()
        if output:
            print(f"YOLO Output: {output.strip()}")
        if process.poll() is not None:
            break

    # Capture final output
    stdout, stderr = process.communicate()
    print(f"\n✅ YOLO Detection Completed!\nOutput: {stdout}")
    if stderr:
        print(f"\n⚠️ Errors (if any): {stderr}")

    context.process = process

@then("I should receive an object detection result")
def step_impl_verify_detection(context):
    """
    Validate the detection results.
    """
    assert context.process.returncode == 0, (
        f"❌ Detection command failed with error: {context.process.stderr}"
    )

    # Wait for output JSON to be generated
    timeout = 30  # Max wait time in seconds
    elapsed = 0
    while not os.path.exists(OUTPUT_JSON_PATH) and elapsed < timeout:
        print(f"⏳ Waiting for output JSON... {elapsed}s elapsed")
        time.sleep(2)
        elapsed += 2

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
