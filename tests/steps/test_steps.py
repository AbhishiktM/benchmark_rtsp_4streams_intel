import json
import subprocess
import os
import time
from behave import given, when, then

MODEL = "yolo11s"
DEVICE = "CPU"
INPUT_VIDEO = "/videos/person-bicycle-car-detection.mp4"
OUTPUT_TYPE = "json"
EXPECTED_OUTPUT_PATH = "/mnt/data/output.json"  # Expected output location
YOLO_SCRIPT_PATH = "/opt/intel/dlstreamer/samples/gstreamer/gst_launch/detection_with_yolo/yolo_detect.sh"
ACTUAL_OUTPUT_PATH = None  # This will be detected dynamically

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

    # Debug: Print actual file locations
    print("\n🔎 Checking essential paths inside container:")
    
    for path in [YOLO_SCRIPT_PATH, INPUT_VIDEO, EXPECTED_OUTPUT_PATH]:
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
        command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
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

    # Step 1: Search for `output.json`
    print("\n🔎 Searching for `output.json` inside the container...")
    result = subprocess.run(["find", "/", "-name", "output.json"], capture_output=True, text=True)
    
    global ACTUAL_OUTPUT_PATH
    ACTUAL_OUTPUT_PATH = result.stdout.strip()  # Get the first found path

    if not ACTUAL_OUTPUT_PATH:
        print("🚨 `output.json` not found in the expected location!")
        subprocess.run(["find", "/", "-name", "output.json"], check=False)
        assert False, "🚨 Output file is missing. Please check the container!"

    print(f"✅ Found `output.json` at: {ACTUAL_OUTPUT_PATH}")

    # Step 2: Print contents of `output.json`
    print("\n📂 Listing `output.json` details:")
    subprocess.run(["ls", "-lh", ACTUAL_OUTPUT_PATH], check=False)

    # Step 3: Validate the detection results
    timeout = 30  # Max wait time in seconds
    elapsed = 0
    while not os.path.exists(ACTUAL_OUTPUT_PATH) and elapsed < timeout:
        print(f"⏳ Waiting for output JSON... {elapsed}s elapsed")
        time.sleep(2)
        elapsed += 2

    assert os.path.exists(ACTUAL_OUTPUT_PATH), f"🚨 Output JSON file not found at {ACTUAL_OUTPUT_PATH}"

    # Read JSON output from the correct location
    try:
        with open(ACTUAL_OUTPUT_PATH, "r") as json_file:
            detection_result = json.load(json_file)
    except json.JSONDecodeError as e:
        assert False, f"🚨 Output is not valid JSON: {e}"
    except FileNotFoundError:
        assert False, "🚨 Output JSON file not found!"

    assert detection_result, "🚨 Detection JSON output is empty"

    print("\n✅ Object detection completed successfully with JSON output:", detection_result)
