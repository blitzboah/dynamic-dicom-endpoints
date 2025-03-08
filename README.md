# Dynamic DICOM Endpoints

This project provides a dynamic DICOM routing system using multiple Orthanc instances. It consists of two Orthanc instances running as PACS servers and one Orthanc instance acting as a probe.

## Architecture

- **Orthanc Storage 1**: First PACS server instance
- **Orthanc Storage 2**: Second PACS server instance
- **Orthanc Probe**: Instance used for routing and monitoring

The system dynamically routes DICOM files to the appropriate storage based on configured rules.

## Prerequisites

- Docker and Docker Compose
- DICOM toolkit (dcmtk) for sending files with StoreSCU command

## Getting Started

### Setup and Installation

1. Clone this repository:
   ```bash
   git clone https://github.com/blitzboah/dynamic-dicom-endpoints.git
   cd dynamic-dicom-endpoints
   ```

2. Start the services using Docker Compose:
   ```bash
   docker-compose up -d
   ```

This will start:
- Two Orthanc PACS servers running on ports 8042 and 8043
- One Orthanc probe instance running on port 8044
- The custom middleware service 

### Sending DICOM Files

To send DICOM files to the system, use the StoreSCU command from the DICOM toolkit:

```bash
storescu -v -aet TEST_SCU -aec DYNAMIC_DICOM_MW localhost 11113 dcm_files/test_file1.dcm
```

You can also send multiple files:

```bash
storescu -v -aet TEST_SCU -aec DYNAMIC_DICOM_MW localhost 11113 dcm_files/*.dcm
```

- The last parameter is the path to the DICOM file(s) to send

## Configuration

The system uses three main configuration files:
- `orthanc_storage_1.json`: Configuration for the first PACS server
- `orthanc_storage_2.json`: Configuration for the second PACS server
- `orthanc_probe.json`: Configuration for the routing probe

## Components

- `main.py`: Entry point for the middleware service
- `middleware.py`: Contains the routing logic
- `orthanc_manager.py`: Manages communication with Orthanc instances
- `dicom_listener.py`: Listens for incoming DICOM files

## Docker Compose Services

The Docker Compose configuration creates the following services:
1. `orthanc-storage-1`: First PACS server
2. `orthanc-storage-2`: Second PACS server
3. `orthanc-probe`: The routing probe
4. `middleware`: The custom routing service

## Troubleshooting

Check the logs for any errors:
```bash
docker-compose logs -f
```

![image](https://github.com/user-attachments/assets/171aac22-05b3-46de-ac4b-3a7639cc9a92)
![image](https://github.com/user-attachments/assets/79da211e-e811-4d37-802b-d7dada279640)


