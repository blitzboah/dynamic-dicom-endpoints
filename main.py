import time
import threading
import sys
import requests
from orthanc_manager import OrthancManager
from middleware import route_dicom_image
from pynetdicom import AE, evt
from pydicom import Dataset

DEBUG_MODE = "--debug" in sys.argv

def log_debug(message):
    """ Print debug messages only if --debug is enabled. """
    if DEBUG_MODE:
        print(message, flush=True)

def log_info(message):
    """ Always print important logs. """
    print(message, flush=True)

def handle_store(event):
    """
    Handle incoming DICOM images.
    """
    log_info("Received a DICOM image.")
    
    ds = event.dataset  # The DICOM dataset
    log_debug(f"SOP Instance UID: {ds.SOPInstanceUID}")

    try:
        log_info("Finding the best Orthanc instance for storage...")
        
        selected_server, instance_count = route_dicom_image(ds, debug=DEBUG_MODE)

        if selected_server:
            log_info(f"Image stored in {selected_server['ae_title']} (Instances: {instance_count})")
        else:
            log_info("No available Orthanc instance found. Image was not stored.")
    except Exception as e:
        log_info(f"ERROR in handle_store: {e}")

    return 0x0000  # Success status

def start_dicom_listener(port=11113):
    """
    Start a DICOM listener on the specified port.
    """
    log_info(f"Starting DICOM listener on port {port}...")
    ae = AE(ae_title='DYNAMIC_DICOM_MW')
    ae.add_supported_context('1.2.840.10008.5.1.4.1.1.2')  # CT image storage
    
    ae.start_server(('', port), evt_handlers=[(evt.EVT_C_STORE, handle_store)])

def auto_sync_orthanc_instances(orthanc_manager, debug=False):
    """
    Automatically sync images from ORTHANC1 & ORTHANC2 to ORTHANC-PROBE.
    """
    while True:
        try:
            instance_counts = orthanc_manager.probe_servers(debug)

            pacs_servers = ["ORTHANC1", "ORTHANC2"]
            probe_server = "ORTHANC-PROBE"

            if probe_server not in instance_counts:
                log_info(f"Skipping sync: Probe {probe_server} is missing from instance counts.")
                continue

            # Sync PACS servers with each other
            if instance_counts["ORTHANC1"] > instance_counts["ORTHANC2"]:
                log_info(f"Syncing ORTHANC1 → ORTHANC2 ({instance_counts['ORTHANC1']} → {instance_counts['ORTHANC2']})")
                instance_list = requests.get(
                    "http://orthanc-storage-1:8042/instances",
                    auth=("orthanc", "orthanc")
                ).json()
                for instance_uid in instance_list:
                    orthanc_manager.retrieve_from_other_orthanc(
                        {"ae_title": "ORTHANC1", "rest_url": "http://orthanc-storage-1:8042"},
                        {"ae_title": "ORTHANC2", "rest_url": "http://orthanc-storage-2:8043"},
                        instance_uid,
                        debug=True
                    )
                log_info("PACS Sync complete.")

            # Sync all PACS servers to the probe
            for pacs in pacs_servers:
                if instance_counts[pacs] > instance_counts[probe_server]:
                    log_info(f"Syncing {pacs} → {probe_server} ({instance_counts[pacs]} → {instance_counts[probe_server]})")
                    instance_list = requests.get(
                        f"http://orthanc-storage-1:8042/instances" if pacs == "ORTHANC1" else f"http://orthanc-storage-2:8043/instances",
                        auth=("orthanc", "orthanc")
                    ).json()
                    for instance_uid in instance_list:
                        orthanc_manager.retrieve_from_other_orthanc(
                            {"ae_title": pacs, "rest_url": f"http://orthanc-storage-1:8042" if pacs == "ORTHANC1" else f"http://orthanc-storage-2:8043"},
                            {"ae_title": probe_server, "rest_url": "http://orthanc-probe:8052"},
                            instance_uid,
                            debug=True
                        )
                    log_info(f"{pacs} → {probe_server} Sync complete.")

            log_info("No additional sync needed.")

        except Exception as e:
            log_info(f"Error during auto-sync: {e}")

        time.sleep(10)  # Wait 10 seconds before next sync check

def start_background_sync():
    """
    Start a background thread to sync Orthanc instances periodically.
    """
    orthanc_servers = [
        {"ae_title": "ORTHANC1", "rest_url": "http://orthanc-storage-1:8042"},
        {"ae_title": "ORTHANC2", "rest_url": "http://orthanc-storage-2:8043"},
    ]
    
    orthanc_probe = {"ae_title": "ORTHANC-PROBE", "rest_url": "http://orthanc-probe:8052"}

    orthanc_manager = OrthancManager(orthanc_servers, orthanc_probe)
    
    sync_thread = threading.Thread(target=auto_sync_orthanc_instances, args=(orthanc_manager, DEBUG_MODE), daemon=True)
    sync_thread.start()
    log_info("Started background Orthanc sync thread.")

if __name__ == "__main__":
    start_background_sync()
    start_dicom_listener()
