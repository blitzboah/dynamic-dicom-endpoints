from pynetdicom import AE, evt, debug_logger
from pydicom import Dataset

def handle_store(event):
    """
    handle incoming DICOM images.
    """
    ds = event.dataset  # the DICOM dataset
    print(f"Received DICOM image with SOP Instance UID: {ds.SOPInstanceUID}")
    
    # pass the dataset to the routing logic
    route_dicom_image(ds)
    
    return 0x0000  # success status

def start_dicom_listener(port=11113):
    """
    Start a DICOM listener on the specified port.
    """
    ae = AE(ae_title='DYNAMIC_DICOM_MW')
    ae.add_supported_context('1.2.840.10008.5.1.4.1.1.2')  # CT image storage
    ae.start_server(('', port), evt_handlers=[(evt.EVT_C_STORE, handle_store)])
    print(f"DICOM listener started on port {port}")

if __name__ == "__main__":
    start_dicom_listener()
