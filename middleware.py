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
        {'ae_title': 'ORTHANC1', 'rest_url': 'http://localhost:8042'},
        {'ae_title': 'ORTHANC2', 'rest_url': 'http://localhost:8052'}
    ]

    log_debug(f"Configured servers: {[s['ae_title'] for s in orthanc_servers]}")

    orthanc_manager = OrthancManager(orthanc_servers)

    try:
        log_debug("Checking server loads...")
        available_servers = []

        for server in orthanc_servers:
            log_debug(f"Checking {server['ae_title']} at {server['rest_url']}/statistics")
            count = orthanc_manager.get_instance_count(server)

            log_debug(f"Response from {server['ae_title']}: {count}")

            if count != float('inf'):
                available_servers.append((server, count))
            else:
                log_debug(f"Server {server['ae_title']} is NOT available")

        if not available_servers:
            print("No available servers found!")
            return None, None
            
        selected_server, instance_count = min(available_servers, key=lambda x: x[1])
        log_debug(f"Selected server: {selected_server['ae_title']} (Instances: {instance_count})")

        temp_file = f"/tmp/{ds.SOPInstanceUID}.dcm"
        log_debug(f"Saving DICOM file to {temp_file}")
        ds.save_as(temp_file)

        log_debug(f"Sending DICOM image to {selected_server['ae_title']} at {selected_server['rest_url']}/instances")
        success = orthanc_manager.send_dicom_image(selected_server, temp_file)

        os.remove(temp_file)
        log_debug(f"Removed temporary file: {temp_file}")

        if success:
            log_debug(f"Successfully sent DICOM image to {selected_server['ae_title']}")
        else:
            log_debug(f"Failed to send DICOM image to {selected_server['ae_title']}")

        return selected_server, instance_count  # Return selected server and instance count

    except Exception as e:
        print(f"Error in routing DICOM image: {e}")
        return None, None

