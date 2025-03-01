from pynetdicom import AE, evt, debug_logger
from pydicom import Dataset
import sys

# Make sure to import the routing function
from middleware import route_dicom_image

def handle_store(event):
    """
    handle incoming DICOM images.
    """
    print("=== STORE event triggered ===", flush=True)
    ds = event.dataset  # the DICOM dataset
    print(f"Received DICOM image with SOP Instance UID: {ds.SOPInstanceUID}", flush=True)
    
    # Explicitly flush stdout to ensure we see output
    sys.stdout.flush()
    
    try:
        # pass the dataset to the routing logic
        print("Calling route_dicom_image function...", flush=True)
        route_dicom_image(ds)
        print("Returned from route_dicom_image function", flush=True)
    except Exception as e:
        print(f"ERROR in handle_store: {e}", flush=True)
    
    # Flush again to ensure we see output
    sys.stdout.flush()
    
    return 0x0000  # success status

def start_dicom_listener(port=11113):
    """
    Start a DICOM listener on the specified port.
    """
    ae = AE(ae_title='DYNAMIC_DICOM_MW')
    ae.add_supported_context('1.2.840.10008.5.1.4.1.1.2')  # CT image storage
    print(f"Starting DICOM listener on port {port}...", flush=True)
    ae.start_server(('', port), evt_handlers=[(evt.EVT_C_STORE, handle_store)])
    print(f"DICOM listener started on port {port}", flush=True)

if __name__ == "__main__":
    start_dicom_listener()
