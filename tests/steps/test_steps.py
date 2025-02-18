import os
import time
import subprocess
from behave import given, when, then

MODEL = "yolo11s"
DEVICE = "CPU"
INPUT_VIDEO = "/videos/person-bicycle-car-detection.mp4"
OUTPUT_TYPE = "json"
YOLO_SCRIPT_PATH = "/opt/intel/dlstreamer/samples/gstreamer/gst_launch/detection_with_yolo/yolo_detect.sh"
EXPECTED_OUTPUT_PATH = "/mnt/data/output.json"  # Expected output location
ACTUAL_OUTPUT_PATH = None  # This will be detected dynamically

@given("the DL Streamer pipeline is running")
def step_impl_pipeline_running(context):
    print("DL Streamer is running inside the container, automatically passing this step.")
    pass

@when("I submit a sample video for detection")
def step_impl_submit_video(context):
    print("\nChecking essential paths inside container:")
    
    for path in [YOLO_SCRIPT_PATH, INPUT_VIDEO, EXPECTED_OUTPUT_PATH]:
        exists = os.path.exists(path)
        print(f"Path: {path} | Exists: {exists}")

    assert os.path.exists(YOLO_SCRIPT_PATH), f"YOLO script not found at {YOLO_SCRIPT_PATH}"
    assert os.path.exists(INPUT_VIDEO), f"Input video not found at {INPUT_VIDEO}"

    command = [YOLO_SCRIPT_PATH, MODEL, DEVICE, INPUT_VIDEO, OUTPUT_TYPE]
    
    print("\nStarting YOLO detection... Waiting for it to complete.")
    
    process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    
    while True:
        output = process.stdout.readline()
        if output:
            print(f"YOLO Output: {output.strip()}")
        if process.poll() is not None:
            break

    stdout, stderr = process.communicate()
    print("\nYOLO Detection Completed!")
    
    if stderr:
        print(f"Errors (if any): {stderr}")

    context.process = process

@then("I should receive an object detection result")
def step_impl_verify_detection(context):
    global ACTUAL_OUTPUT_PATH

    print("\nSearching for `output.json` inside the container...")
    result = subprocess.run(["find", "/", "-name", "output.json"], capture_output=True, text=True)
    ACTUAL_OUTPUT_PATH = result.stdout.strip()

    if not ACTUAL_OUTPUT_PATH:
        print("`output.json` not found in the expected location!")
        subprocess.run(["find", "/", "-name", "output.json"], check=False)
        assert False, "Output file is missing. Please check the container!"

    print(f"Found `output.json` at: {ACTUAL_OUTPUT_PATH}")

    # Test passes if `output.json` exists
    assert os.path.exists(ACTUAL_OUTPUT_PATH), f"Output JSON file not found at {ACTUAL_OUTPUT_PATH}"
    print("\nTest passed: `output.json` is present.")
