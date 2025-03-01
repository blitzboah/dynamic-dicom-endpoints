import requests

class OrthancManager:
    def __init__(self, orthanc_servers):
        """
        Initialize with a list of Orthanc servers.
        """
        self.orthanc_servers = orthanc_servers

    def get_instance_count(self, server):
        """
        Get the number of instances in a specific Orthanc server.
        """
        try:
            response = requests.get(f"{server['rest_url']}/statistics")
            return response.json().get('CountInstances', float('inf')) if response.ok else float('inf')
        except requests.RequestException:
            return float('inf')

    def send_dicom_image(self, server, dicom_file):
        """
        Send a DICOM image to a specific Orthanc server.
        """
        try:
            with open(dicom_file, 'rb') as f:
                response = requests.post(f"{server['rest_url']}/instances", data=f)
                return response.status_code == 200
        except requests.RequestException:
            return False
