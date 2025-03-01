## Dynamic DICOM Endpoints

## Overview
This project dynamically routes DICOM data to multiple Orthanc servers based on queue load and performance. It can be used for teleradiology, federated learning, or distributed PACS (Picture Archiving and Communication System) setups. The system enables dynamic load balancing across multiple Orthanc instances.

---

## Dependencies
Before running the setup, ensure you have the following installed:

- **Docker** (for running Orthanc instances)
- **DCMTK** (for sending DICOM images using `storescu`)
- **curl** (for checking stored instances)

Install dependencies:
```bash
sudo apt update && sudo apt install docker.io dcmtk curl -y
```

---

## Running with Docker
### 1️⃣ Start Multiple Orthanc Instances
Run the following Docker commands to start two Orthanc instances:
```bash
sudo docker run -d --rm --name orthanc1 -p 8042:8042 -p 4242:4242 jodogne/orthanc-plugins
sudo docker run -d --rm --name orthanc2 -p 8052:8042 -p 4252:4242 jodogne/orthanc-plugins
```

Check if the instances are running:
```bash
docker ps
```

---

## Sending a DICOM File Using `storescu`
Once Orthanc is running, send a test DICOM file to the middleware listener.

1️⃣ **Install `dcmtk` (if not installed)**:
```bash
sudo apt install dcmtk -y  # Ubuntu/Debian
sudo pacman -S dcmtk        # Arch Linux
```

2️⃣ **Send a DICOM image using `storescu`**:
```bash
storescu -v -aec ANY-SCP localhost 11113 /path/to/test.dcm
```
- **`-aec ANY-SCP`** → The AE Title for the receiving application.
- **`localhost 11113`** → The middleware listener port.
- **`/path/to/test.dcm`** → Replace with your actual DICOM file.

---

## Checking Stored Instances in Orthanc
To verify if the image was stored in one of the Orthanc servers, use:

1️⃣ **Check Orthanc1:**
```bash
curl -u orthanc:orthanc http://localhost:8042/instances
```

2️⃣ **Check Orthanc2:**
```bash
curl -u orthanc:orthanc http://localhost:8052/instances
```

If an instance ID appears, the DICOM file was successfully stored.

---

## Conclusion
This setup supports **automatic routing and load balancing** for DICOM endpoints. You can:
- Use **Docker** for running Orthanc instances.
- Use **storescu** to send DICOM files.
- Use **curl** to verify stored instances.

Next steps can include **HAProxy** or **Lua scripting** for advanced dynamic routing.

 dynamic-dicom-endpoints
