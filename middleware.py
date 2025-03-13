import os
from orthanc_manager import OrthancManager

def route_dicom_image(ds, debug=False):
    """
    Route the DICOM image to the least loaded Orthanc server.
    Returns (selected_server, instance_count).
    """
    def log_debug(msg):
        if debug:
            print(msg, flush=True)

    log_debug("Starting DICOM routing...")

    orthanc_servers = [
        {"ae_title": "ORTHANC1", "rest_url": "http://orthanc-storage-1:8042"},
        {"ae_title": "ORTHANC2", "rest_url": "http://orthanc-storage-2:8043"},
    ]

    orthanc_probe = {"ae_title": "ORTHANC-PROBE", "rest_url": "http://orthanc-probe:8052"}

    # Initialize Orthanc Manager with two PACS servers and one probe
    orthanc_manager = OrthancManager(orthanc_servers, orthanc_probe)

    log_debug(f"Configured servers: {[s['ae_title'] for s in orthanc_servers]}")

    # Explicitly probe before making a decision
    instance_counts = orthanc_manager.probe_servers(debug=debug)

    available_servers = []
    for server in orthanc_servers:
        count = instance_counts.get(server["ae_title"], float("inf"))
        if count >= 0:
            available_servers.append((server, count))

    if not available_servers:
        print("No available servers found!")
        return None, None
            
    selected_server, instance_count = min(available_servers, key=lambda x: x[1])
    log_debug(f"Selected server: {selected_server['ae_title']} (Instances: {instance_count})")

    temp_file = f"/tmp/{ds.SOPInstanceUID}.dcm"
    log_debug(f"Saving DICOM file to {temp_file}")
    ds.save_as(temp_file)

    log_debug(f"Sending DICOM image to {selected_server['ae_title']} at {selected_server['rest_url']}/instances")
    success, ae_title = orthanc_manager.send_dicom_image(selected_server, temp_file)

    os.remove(temp_file)
    log_debug(f"Removed temporary file: {temp_file}")

    if success:
        log_debug(f"Successfully sent DICOM image to {selected_server['ae_title']}")
    else:
        log_debug(f"Failed to send DICOM image to {selected_server['ae_title']}")
    
    if success:
        return ae_title, instance_count
    else:
        return None, None
