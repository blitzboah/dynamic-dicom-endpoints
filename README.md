# Dynamic DICOM Endpoints

## Overview
This project dynamically routes DICOM data to multiple Orthanc servers based on queue load and performance. It can be used for teleradiology, federated learning, or distributed PACS (Picture Archiving and Communication System) setups. The system enables dynamic load balancing across multiple Orthanc instances.

## Dependencies
Before running the setup, ensure you have the following installed:

- **Docker** (for running Orthanc instances)
- **DCMTK** (for sending DICOM images using `storescu`)
- **curl** (for checking stored instances)
- **Python 3** (for additional scripts)
- **pydicom** and **requests** (for handling DICOM modifications)

### Install Dependencies
```bash
sudo apt update && sudo apt install docker.io dcmtk curl -y
pip install pydicom requests
```

## Running the Middleware (main.py)
The middleware listens for incoming DICOM images and routes them to the least-loaded Orthanc instance.

### Start Middleware (Normal Mode)
```bash
python main.py
```

This will:
- Start the DICOM listener on port 11113.
- Log essential messages like image received and selected Orthanc instance.
- It will not show debug details.

### Start Middleware (Debug Mode)
```bash
python main.py --debug
```

This will:
- Show detailed logs about DICOM routing.
- Include instance counts from each Orthanc server.
- Display all network requests made to Orthanc.

## Running with Docker

### Start Multiple Orthanc Instances
Run the following Docker commands to start two Orthanc instances:

```bash
sudo docker run -d --rm --name orthanc1 -p 8042:8042 -p 4242:4242 jodogne/orthanc-plugins
sudo docker run -d --rm --name orthanc2 -p 8052:8042 -p 4252:4242 jodogne/orthanc-plugins
```

Check if the instances are running:

```bash
docker ps
```

## Sending a DICOM File Using storescu
Once Orthanc is running, send a test DICOM file to the middleware listener.

### Install dcmtk (if not installed)
```bash
sudo apt install dcmtk -y  # Ubuntu/Debian
sudo pacman -S dcmtk        # Arch Linux
```

### Send a DICOM image using storescu
```bash
storescu -v -aec ANY-SCP localhost 11113 /path/to/test.dcm
```
- `-aec ANY-SCP` → The AE Title for the receiving application.
- `localhost 11113` → The middleware listener port.
- `/path/to/test.dcm` → Replace with your actual DICOM file.

## Checking Stored Instances in Orthanc
To verify if the image was stored in one of the Orthanc servers, use:

### Check Orthanc1
```bash
curl -u orthanc:orthanc http://localhost:8042/instances
```

### Check Orthanc2
```bash
curl -u orthanc:orthanc http://localhost:8052/instances
```

If an instance ID appears, the DICOM file was successfully stored.

## Testing with Multiple DICOM Files
You can send multiple DICOM files at once:

```bash
storescu -v -aec ANY-SCP localhost 11113 dcm_files/*.dcm
```

If some files fail with "SOPClassUID is missing" errors, follow the next section.

## Fixing DICOM Files (Missing SOPClassUID)
If some DICOM files fail to send due to missing SOPClassUID, use fix_sop_uid.py:

### Run the script
```bash
python fix_sop_uid.py
```

### What it does
- Fixes missing SOPClassUID
- Assigns a new SOPInstanceUID to avoid duplicates
- Saves the corrected DICOM files

### Resend the fixed DICOM files
```bash
storescu -v -aec ANY-SCP localhost 11113 dcm_files/*.dcm
```

## Deleting All DICOM Files
If you need to delete all stored DICOM images from Orthanc instances:

### Use the delete script
```bash
python delete_all_dicom.py
```

### Alternatively, delete manually using cURL
```bash
curl -u orthanc:orthanc -X DELETE http://localhost:8042/instances
curl -u orthanc:orthanc -X DELETE http://localhost:8052/instances
```

This will remove all stored DICOM images.

## Conclusion
This setup supports automatic routing and load balancing for DICOM endpoints. You can:

- Use Docker for running Orthanc instances.
- Use storescu to send DICOM files.
- Use curl to verify stored instances.
- Use Python scripts to fix or delete DICOM images.