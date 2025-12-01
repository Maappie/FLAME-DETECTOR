# Flame Vision
### Real-Time Fire Detection & Automated Suppression System

Flame Vision is an intelligent safety system designed to detect fire hazards instantly using Computer Vision (CV) and Deep Learning. Unlike traditional smoke detectors, this system identifies flames visually from live camera feeds and autonomously triggers suppression hardware (sprinklers) via an ESP32 microcontroller, ensuring rapid response times to prevent property damage.

---

## Key Features

- Real-Time Detection: Uses deep learning algorithms to identify fire/flames in video streams with high accuracy and low latency.
- Automated Suppression: Directly communicates with ESP32 hardware to trigger relays for sprinklers or alarms immediately upon detection.
- Hybrid Connectivity: Implements a robust communication architecture using MQTT, HTTP, and ZeroMQ (0MQ) for seamless data transfer between the vision server and edge devices.
- Visual Localization: Identifies the specific location of the fire within the frame for targeted monitoring.

---

## Tech Stack

### Software & AI
- Language: Python (Computer Vision), C++ (Embedded)
- Computer Vision: OpenCV, YOLOv8 (or MobileNet SSD)
- Communication Protocols:
    - MQTT: For lightweight, machine-to-machine messaging.
    - ZeroMQ (0MQ): For high-speed asynchronous messaging (used in camera feed, Vision Node to System dashboard).
    - HTTP: For standard web requests and logging.

### Hardware
- Microcontroller: ESP32 (Wi-Fi enabled)
- Camera: Webcam
- Actuators: Relay Module (controlling Sprinklers/Alarms)
- Sensor: MQ2-gas Sensor

---

## System Architecture

1. Vision Node: The camera feed is processed by the main computer/server running the Deep Learning model.
2. Decision Logic: When fire is detected (confidence score > threshold), the Vision Node generates the trigger signal and publishes a message (containing location) to a designated MQTT Topic.
3. Transmission: The signal is sent via MQTT to the ESP32 client.
4. Action: The ESP32 receives the payload and activates the GPIO pins connected to the suppression system.

---
