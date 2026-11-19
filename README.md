# SOME-IP
# Multi-ECU Service-Oriented Communication Using SOME/IP

### Virtual Vehicle Communication Network Using Python and someipy

**Project:** Assignment 2 – SOME/IP Multi-ECU Communication  
**Platform:** Ubuntu Linux  
**Programming Language:** Python 3.12  
**Protocol:** SOME/IP (Scalable Service-Oriented Middleware over IP)  
**Library:** someipy 2.1.2  
**Network Analysis:** Wireshark  
**Version Control:** Git and GitHub  

**GitHub Repository:** https://github.com/Pushkar4568/SOME-IP

---

## 1. Project Overview

This project demonstrates Service-Oriented Architecture (SOA) in automotive communication using the SOME/IP protocol.

Modern vehicles contain multiple Electronic Control Units (ECUs) responsible for functions such as vehicle speed monitoring, climate control, instrument cluster displays, and central infotainment systems.

Traditionally, ECUs exchange information using protocols such as CAN. SOME/IP enables service-oriented communication over automotive Ethernet/IP networks.

In this project, four virtual ECUs communicate over a simulated vehicle network using Python and the `someipy` library.

The project demonstrates:

- Multiple virtual ECUs
- Multiple SOME/IP services
- Service Providers and Service Consumers
- SOME/IP Service Discovery
- Request-response communication
- Publish-subscribe communication
- Method invocation
- Events and event groups
- Multiple consumers using one service
- One consumer using multiple services
- Input validation
- Service failure and recovery
- Packet analysis using Wireshark

The ECUs are implemented as independent Python applications running in separate Ubuntu terminals.

## 2. Project Objectives

The primary objective is to design and implement a small virtual automotive network using SOME/IP.

Specific objectives include:

1. Create four independent virtual ECUs.
2. Implement two SOME/IP services.
3. Establish communication between Service Providers and Consumers.
4. Implement synchronous-style request-response method calls using asynchronous Python.
5. Implement event-based publish-subscribe communication.
6. Discover services dynamically using SOME/IP Service Discovery.
7. Generate overspeed warnings when vehicle speed exceeds 80 km/h.
8. Validate cabin temperature requests.
9. Observe service availability and recovery.
10. Capture and analyze network packets using Wireshark.

## 3. System Architecture

The system contains four logical ECUs.

```text
                 VIRTUAL VEHICLE NETWORK
                 =======================

      +--------------------+  +--------------------+
      |    VEHICLE ECU     |  |     CLIMATE ECU    |
      |   Service Provider |  |   Service Provider |
      |                    |  |                    |
      | VehicleSpeedService|  |   ClimateService   |
      |   ID: 0x1234       |  |    ID: 0x2234      |
      +---------+----------+  +----------+---------+
                |                        |
                |                        |
                |        SOME/IP         |
                |       over UDP         |
                |                        |
                +------------+-----------+
                |            |
                v            v
      +----------------+  +---------------------+
      |  INSTRUMENT    |  |    CENTRAL DISPLAY  |
      |   CLUSTER ECU  |  |          ECU        |
      |                |  |                     |
      | Speed Consumer |  | Vehicle Consumer    |
      |                |  | Climate Consumer    |
      +----------------+  +---------------------+
```

### ECU Responsibilities

| ECU | Role | Responsibility |
|---|---|---|
| Vehicle ECU | Provider | Simulates vehicle speed and vehicle state |
| Instrument Cluster | Consumer | Displays speed and overspeed warnings |
| Climate ECU | Provider | Simulates cabin temperature and controls target temperature |
| Central Display | Consumer | Consumes both VehicleSpeedService and ClimateService |

The Vehicle ECU provides data to two consumers simultaneously.

The Central Display communicates with two independent service providers.

## 4. What is SOME/IP?

SOME/IP stands for **Scalable Service-Oriented Middleware over IP**.

It is an automotive communication protocol used to exchange information between software applications and ECUs over IP networks.

SOME/IP supports:

- Method-based request-response communication
- Event notifications
- Publish-subscribe communication
- Serialization and deserialization
- UDP and TCP transport

### SOME/IP Service Discovery

SOME/IP Service Discovery (SOME/IP-SD) allows Service Providers to announce the availability of services and enables consumers to find them dynamically.

A consumer does not need to assume that a service is always available.

The typical communication process is:

```text
Service Provider
       |
       | OfferService
       v
SOME/IP Service Discovery
       |
       | Service becomes available
       v
Service Consumer
       |
       | Request / Subscribe
       v
Service Provider
       |
       | Response / Notification
       v
Service Consumer
```

In this project, the `someipyd` daemon supports service discovery and SOME/IP communication.

## 5. VehicleSpeedService

The Vehicle ECU implements the VehicleSpeedService.

### Service Configuration

| Parameter | Value |
|---|---|
| Service Name | VehicleSpeedService |
| Service ID | 0x1234 |
| Instance ID | 0x5678 |
| Major Version | 1 |
| Transport Protocol | UDP |
| Endpoint | 127.0.0.1:3000 |

### Methods

**GetSpeed()**

| Parameter | Value |
|---|---|
| Method ID | 0x0001 |
| Request Payload | Empty |
| Response | Current vehicle speed |
| Data Type | uint16 |
| Unit | km/h |

The consumer requests the current speed, and the Vehicle ECU responds with the latest simulated value.

**GetVehicleState()**

| Parameter | Value |
|---|---|
| Method ID | 0x0002 |
| Request Payload | Empty |
| Response | Vehicle state |
| Data Type | uint8 |

Vehicle state is determined from speed:

```python
if current_speed_kmph == 0:
    state = 0  # STOPPED
else:
    state = 1  # MOVING
```

### Events

**SpeedChanged**

| Parameter | Value |
|---|---|
| Event ID | 0x8001 |
| Event Group ID | 0x0001 |
| Data Type | uint16 |

The Vehicle ECU publishes a SpeedChanged notification whenever the simulated speed changes.

Both the Instrument Cluster and Central Display subscribe to this event group.

**OverspeedWarning**

| Parameter | Value |
|---|---|
| Event ID | 0x8002 |
| Event Group ID | 0x0002 |
| Data Type | uint16 |
| Trigger | Speed greater than 80 km/h |

The warning condition is:

```python
if current_speed_kmph > 80:
    # Publish OverspeedWarning
```

Expected behavior:

| Speed | SpeedChanged | OverspeedWarning |
|---|---|---|
| 50 km/h | Yes | No |
| 70 km/h | Yes | No |
| 80 km/h | Yes | No |
| 90 km/h | Yes | Yes |
| 100 km/h | Yes | Yes |

At exactly 80 km/h, no warning is generated because the condition uses `>` rather than `>=`.

## 6. ClimateService

The Climate ECU provides a second independent SOME/IP service.

### Service Configuration

| Parameter | Value |
|---|---|
| Service Name | ClimateService |
| Service ID | 0x2234 |
| Instance ID | 0x0001 |
| Major Version | 1 |
| Transport | UDP |
| Endpoint | 127.0.0.1:3002 |

### Methods

**GetCabinTemperature()**

| Parameter | Value |
|---|---|
| Method ID | 0x0001 |
| Request Payload | Empty |
| Response | Current cabin temperature |
| Data Type | int16 |

Temperatures are represented in tenths of a degree Celsius.

Examples:

```text
240 = 24.0°C
245 = 24.5°C
250 = 25.0°C
```

This allows decimal temperature values to be communicated using integer payloads.

**SetTargetTemperature()**

| Parameter | Value |
|---|---|
| Method ID | 0x0002 |
| Request | Target temperature |
| Request Type | int16 |
| Response | Validation status |
| Response Type | uint8 |

The valid temperature range is 16.0°C to 30.0°C.

The provider validates each incoming request.

```python
if 160 <= requested <= 300:
    target_temperature = requested
    status = 0
else:
    status = 1
```

Response status:

```text
0 = ACCEPTED
1 = INVALID_TEMPERATURE
```

### Temperature Validation

| Requested Temperature | Encoded Value | Expected Result |
|---|---|---|
| 22.0°C | 220 | ACCEPTED |
| 16.0°C | 160 | ACCEPTED |
| 30.0°C | 300 | ACCEPTED |
| 10.0°C | 100 | INVALID_TEMPERATURE |
| 35.0°C | 350 | INVALID_TEMPERATURE |

An invalid request does not modify the existing target temperature.

### CabinTemperatureChanged Event

| Parameter | Value |
|---|---|
| Event ID | 0x8001 |
| Event Group ID | 0x0001 |
| Payload | Cabin temperature |
| Data Type | int16 |

The Climate ECU simulates changes such as:

```text
24.0°C
24.5°C
25.0°C
25.5°C
26.0°C
```

Whenever the value changes, a CabinTemperatureChanged notification is published.

The Central Display subscribes to this event.

## 7. Project File Structure

```text
SOMEIP-Multi-ECU-Project/
|
|-- src/
|   |-- vehicle_speed_interface.py
|   |-- vehicle_speed_service.py
|   |-- cluster_client.py
|   |-- climate_interface.py
|   |-- climate_service.py
|   |-- central_display.py
|
|-- captures/
|   |-- assignment2-multi-ecu.pcapng
|       (Add after saving the Wireshark capture)
|
|-- screenshots/
|   (Add demonstration screenshots)
|
|-- tests/
|   (Reserved for automated tests)
|
|-- requirements.txt
|-- .gitignore
|-- README.md
```

### Explanation of Python Files

| File | Purpose |
|---|---|
| vehicle_speed_interface.py | Defines vehicle service, methods, events and IDs |
| vehicle_speed_service.py | Implements Vehicle ECU service provider |
| cluster_client.py | Implements Instrument Cluster consumer |
| climate_interface.py | Defines climate service, methods and events |
| climate_service.py | Implements Climate ECU service provider |
| central_display.py | Consumes VehicleSpeedService and ClimateService |

## 8. Technologies Used

**Python:** Implements all virtual ECU applications and simulated vehicle functionality.

**someipy:** Provides SOME/IP service definitions, method communication, events and daemon integration.

**Ubuntu Linux:** Hosts the four virtual ECU applications.

**Wireshark:** Captures and analyzes network traffic.

**Git:** Tracks source code changes.

**GitHub:** Stores the source code and project documentation.

## 9. Installation and Setup

### Prerequisites

- Ubuntu Linux
- Python 3
- Python virtual environment support
- Git
- Wireshark
- someipy 2.1.2
- VS Code (optional)

### Clone Repository

```bash
git clone https://github.com/Pushkar4568/SOME-IP.git
cd SOME-IP
```

### Create Virtual Environment

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### Install Dependencies

```bash
pip install someipy==2.1.2
```

The project requires the `someipy` package. Python's `asyncio` and `struct` modules are part of the standard library.

## 10. Running the Project

The system requires one daemon process and four independent ECU applications.

Open five Ubuntu terminals in the project directory.

Activate the Python environment in each terminal:

```bash
source .venv/bin/activate
```

### Terminal 1 — SOME/IP Daemon

```bash
someipyd
```

The daemon uses the configuration established for the local SOME/IP environment.

### Terminal 2 — Vehicle ECU

```bash
python src/vehicle_speed_service.py
```

### Terminal 3 — Instrument Cluster ECU

```bash
python src/cluster_client.py
```

### Terminal 4 — Climate ECU

```bash
python src/climate_service.py
```

### Terminal 5 — Central Display ECU

```bash
python src/central_display.py
```

All applications communicate using the local loopback interface.

## 11. Communication Flow

### Request-Response Communication

Example: GetSpeed()

```text
Instrument Cluster ECU               Vehicle ECU
         |                                |
         |--------- GetSpeed() ---------->|
         |                                |
         |<-------- Speed = 60 -----------|
         |                                |
```

A method is appropriate because the consumer explicitly requests information and expects a response.

### Publish-Subscribe Communication

Example: SpeedChanged

```text
                    Vehicle ECU
                         |
                 SpeedChanged Event
                         |
              +----------+----------+
              |                     |
              v                     v
      Instrument Cluster      Central Display
```

An event is appropriate because subscribers need automatic updates when data changes.

### Multiple Service Consumption

```text
VehicleSpeedService --------+
                            |
                            v
                      Central Display
                            ^
                            |
ClimateService -------------+
```

The Central Display uses both services without duplicating their underlying data.

## 12. Observed Application Results

During development, the applications were executed in separate Ubuntu terminals.

The following functionality was observed:

- VehicleSpeedService became available to consumers.
- GetSpeed returned vehicle speed.
- GetVehicleState returned MOVING.
- SpeedChanged notifications were received.
- OverspeedWarning notifications were received above 80 km/h.
- Climate ECU generated temperature-change notifications.
- Central Display received vehicle and climate information.
- Valid target-temperature requests returned ACCEPTED.

The implementation also includes invalid-temperature rejection. Its response should be demonstrated separately using 10.0°C and 35.0°C requests.

## 13. Service Failure and Recovery Testing

This experiment demonstrates that independent service providers can become unavailable without requiring unrelated services to stop.

### Experiment A — Stop Climate ECU

1. Start all four ECU applications.
2. Confirm that both services are available.
3. Stop Climate ECU using Ctrl+C.
4. Observe the Central Display.
5. Verify that VehicleSpeedService remains functional.
6. Restart Climate ECU.
7. Check whether the climate service becomes available again.

### Experiment B — Stop Vehicle ECU

1. Keep the Climate ECU and both consumers running.
2. Stop Vehicle ECU.
3. Observe VehicleSpeedService availability.
4. Confirm whether ClimateService continues responding.
5. Restart Vehicle ECU.
6. Observe rediscovery and resumed communication.

**Important:** Service failure/recovery observations must be recorded from actual application logs or Wireshark captures. The steps above describe the test procedure, not results that have already been verified.

## 14. Wireshark Packet Analysis

Wireshark is used to observe actual network packets exchanged by the virtual ECUs.

All applications use localhost (`127.0.0.1`), so packets are captured on Ubuntu's loopback interface.

### Capture Procedure

1. Open Wireshark.
2. Select the `lo` (Loopback) interface.
3. Start packet capture.
4. Start the daemon and ECU applications.
5. Observe UDP traffic.
6. Stop capture and save the file.

### Useful Wireshark Display Filter

```text
udp.port == 30490 || udp.port == 3000 ||
udp.port == 3001 || udp.port == 3002 ||
udp.port == 3003 || udp.port == 3004
```

For decoded SOME/IP traffic:

```text
someip
```

Wireshark may require UDP traffic on nonstandard ports to be decoded explicitly as SOME/IP.

### Important Network Values

| Parameter | Value |
|---|---|
| Localhost IP | 127.0.0.1 |
| SOME/IP-SD Multicast Address | 224.224.224.245 |
| SOME/IP-SD Port | 30490 |
| Vehicle ECU Port | 3000 |
| Instrument Cluster Port | 3001 |
| Climate ECU Port | 3002 |
| Central Display Vehicle Port | 3003 |
| Central Display Climate Port | 3004 |

### Fields to Analyze

Representative SOME/IP packets can contain:

- Source IP address
- Destination IP address
- Source UDP port
- Destination UDP port
- Service ID
- Method ID or Event ID
- Client ID
- Session ID
- Protocol version
- Interface version
- Message type
- Return code
- Payload

### SOME/IP Message Types

| Type | Purpose |
|---|---|
| REQUEST | Consumer requests a method operation |
| RESPONSE | Provider returns a method result |
| NOTIFICATION | Provider publishes an event |

The Service ID identifies the service, while the Method/Event ID identifies the operation within that service.

For example, VehicleSpeedService and ClimateService both contain an event with ID `0x8001`.

They are distinguished using their Service IDs:

```text
0x1234 + 0x8001 = SpeedChanged

0x2234 + 0x8001 = CabinTemperatureChanged
```

## 15. Why Methods and Events Are Used

### Methods

Methods are used when a consumer explicitly requests data or asks the provider to perform an operation.

Examples:

- GetSpeed()
- GetVehicleState()
- GetCabinTemperature()
- SetTargetTemperature()

The consumer initiates communication and expects a response.

### Events

Events are used when the provider publishes information to subscribed consumers.

Examples:

- SpeedChanged
- OverspeedWarning
- CabinTemperatureChanged

Subscribers receive notifications without initiating a new request for every update.

### Event Groups

An event group is a collection of events managed for subscription purposes.

Consumers subscribe to event groups to receive the corresponding event notifications.

This supports publisher-subscriber communication and reduces the need for continuous method polling for every data update.


## 19. Conclusion

This mini-project implements a virtual automotive service-oriented communication network using Python and the someipy library.

Four independent ECUs communicate using two SOME/IP services.

The Vehicle ECU provides vehicle speed, vehicle state and overspeed warning functionality, while the Climate ECU provides cabin temperature monitoring and target-temperature control.

The Instrument Cluster demonstrates consumption of VehicleSpeedService, while the Central Display demonstrates consumption of multiple independent services.

The project illustrates how SOME/IP supports modular automotive communication through methods, events, event groups and Service Discovery.

It provides a practical foundation for understanding service-oriented automotive Ethernet systems.

---

## 20. Repository

**Project:** Multi-ECU Service-Oriented Communication Using SOME/IP

**Author:** Pushkar4568

**GitHub:** https://github.com/Pushkar4568/SOME-IP

**Assignment:** Multi-ECU Service-Oriented Communication Using SOME/IP

**Technology:** Python, someipy, Ubuntu Linux, Wireshark, Git and GitHub
