import requests

class OrthancManager:
    def __init__(self, orthanc_servers):
        self.orthanc_servers = orthanc_servers

    def get_instance_count(self, server, debug=False):
        """ Get the number of instances in a specific Orthanc server. """
        try:
            url = f"{server['rest_url']}/statistics"
            if debug:
                print(f"Checking Orthanc at: {url}")

            response = requests.get(url, auth=("orthanc", "orthanc"))

            if debug:
                print(f"HTTP Status: {response.status_code}")

            if response.ok:
                data = response.json()
                if debug:
                    print(f"Response from {server['ae_title']}: {data}")
                return data.get('CountInstances', float('inf'))
            else:
                if debug:
                    print(f"Failed to fetch {server['ae_title']} - HTTP {response.status_code}")
                return float('inf')

        except requests.RequestException as e:
            if debug:
                print(f"Error connecting to {server['ae_title']}: {e}")
            return float('inf')

    def send_dicom_image(self, server, dicom_file, debug=False):
        """ Send a DICOM image to a specific Orthanc server. """
        try:
            url = f"{server['rest_url']}/instances"
            if debug:
                print(f"Sending DICOM image to {url}")

            with open(dicom_file, 'rb') as f:
                response = requests.post(
                    url,
                    data=f,
                    headers={"Content-Type": "application/dicom"},
                    auth=("orthanc", "orthanc")
                )

            if debug:
                print(f"HTTP Status: {response.status_code}, Response: {response.text}")

            return response.status_code == 200

        except requests.RequestException as e:
            if debug:
                print(f"Error sending DICOM image: {e}")
            return False
