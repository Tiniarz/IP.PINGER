# IP_PINGER

![Made with Python](https://img.shields.io/badge/Made%20with-Python-1f425f.svg)
![License GPL v3](https://img.shields.io/badge/License-GPL%20v3-blue.svg)
![Status Active](https://img.shields.io/badge/Status-Active-brightgreen.svg)

A customizable terminal-based network diagnostics and connection stress-testing tool built in Python. It features custom payload generation, real-time latency auditing, multithreaded port scanning capabilities, and persistence mechanisms to ensure the interface stays open after process completion or unhandled runtime faults.

---

## Technical Features

* **Terminal Persistence:** Designed to completely intercept exit signals, invalid entries, and execution completions, forcing the application instance to remain active for log evaluation.
* **Granular Payload Structuring:** Supports structural variability across network diagnostic packets including alphanumeric arrays, null bytes (\x00), high-bit frames (\xff), and uppercase matrices.
* **Multithreaded Mapping:** Concurrently maps local transport layers across standard protocols using non-blocking asynchronous socket routines.
* **Dynamic Latency Evaluation:** Aggregates granular execution diagnostics including jitter, statistical distribution variances, standard deviations, and connection drop timelines.

---

## Environment Setup

### System Prerequisites
Ensure Python 3.8 or higher is correctly provisioned within your local execution variables. The script relies on raw transport layer abstractions provided natively via standard libraries.

### Variable Provisioning
Deploy the command-line interface coloring utilities via your local package management infrastructure:

pip install colorama

---

## Execution Framework

To launch the utility inside a dedicated terminal layer or virtualization interface, initialize the runtime file:

python IP_PINGER.py
