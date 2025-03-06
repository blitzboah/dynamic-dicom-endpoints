from pynetdicom import AE, evt
from pydicom import Dataset
import sys
from middleware import route_dicom_image

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

if __name__ == "__main__":
    start_dicom_listener()
