Feature: Object Detection Pipeline

  Scenario: Process a sample video
    Given the DL Streamer pipeline is running
    When I submit a sample video for detection
    Then I should receive an object detection result
