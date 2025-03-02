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

---

## Sending a DICOM File Using `storescu`
Once Orthanc is running, send a test DICOM file to the middleware listener.

**Install `dcmtk` (if not installed)**:
```bash
sudo apt install dcmtk -y  # Ubuntu/Debian
sudo pacman -S dcmtk        # Arch Linux
```

**Send a DICOM image using `storescu`**:
```bash
storescu -v -aec ANY-SCP localhost 11113 /path/to/test.dcm
```
- **`-aec ANY-SCP`** → The AE Title for the receiving application.
- **`localhost 11113`** → The middleware listener port.
- **`/path/to/test.dcm`** → Replace with your actual DICOM file.

---

## Checking Stored Instances in Orthanc
To verify if the image was stored in one of the Orthanc servers, use:

**Check Orthanc1:**
```bash
curl -u orthanc:orthanc http://localhost:8042/instances
```

**Check Orthanc2:**
```bash
curl -u orthanc:orthanc http://localhost:8052/instances
```

If an instance ID appears, the DICOM file was successfully stored.

---
## Outputs
![image](https://github.com/user-attachments/assets/a12694d7-78ae-4b66-b2d8-c7c366479242)

---

## Future Scope

1. Advanced Load Balancing with HAProxy
Currently, routing decisions are made based on queue size. Future work could implement HAProxy to dynamically balance DICOM storage and retrieval requests.

2. Metadata-Based Routing
Rather than routing purely based on server load, metadata such as modality type (CT, MRI, X-ray) and priority tags can be used to send scans to specialized servers.

3. Scalability with Kubernetes
Deploying Orthanc servers as Kubernetes pods would allow automatic scaling based on workload, ensuring optimal performance.

4. Automated Fault Tolerance
Future iterations could implement automatic failover mechanisms, ensuring that if one Orthanc server crashes, images are redirected seamlessly to another available node.

---

## Conclusion

This setup supports automatic routing and load balancing for DICOM endpoints. You can:
Use Docker for running Orthanc instances.
Use storescu to send DICOM files.
Use curl to verify stored instances.
