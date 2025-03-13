import requests

class OrthancManager:
    def __init__(self, orthanc_servers, probe_server):
        """
        Initialize the Orthanc manager with PACS servers and the probe server.
        """
        self.orthanc_servers = orthanc_servers  # List of PACS servers (ORTHANC1, ORTHANC2)
        self.probe_server = probe_server  # Probe server (ORTHANC-PROBE)

    def get_instance_count(self, server, debug=False):
        """
        Get the number of instances (DICOM images) in a specific Orthanc server.
        """
        try:
            url = f"{server['rest_url']}/statistics"
            if debug:
                print(f"Probing {server['ae_title']} at: {url}")

            response = requests.get(url, auth=("orthanc", "orthanc"))

            if response.ok:
                data = response.json()
                count = data.get("CountInstances", float("inf"))
                if debug:
                    print(f"Response from {server['ae_title']}: {count} instances")
                return count
            else:
                return float("inf")  # Server unreachable

        except requests.RequestException as e:
            if debug:
                print(f"Error connecting to {server['ae_title']}: {e}")
            return float("inf")

    def probe_servers(self, debug=False):
        """ Probe all configured Orthanc servers including the probe. """
        results = {}
    
        for server in self.orthanc_servers:
            count = self.get_instance_count(server, debug)
            results[server["ae_title"]] = count

        probe_count = self.get_instance_count(self.probe_server, debug)
        results[self.probe_server["ae_title"]] = probe_count

        return results

    def send_dicom_image(self, server, dicom_file, debug=False):
        """
        Send a DICOM image to a specific PACS server.
        """
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

            if response.status_code == 200:
                return True, server["ae_title"]
            else:
                return False, None

        except requests.RequestException as e:
            if debug:
                print(f"Error sending DICOM image: {e}")
            return False

    def retrieve_from_other_orthanc(self, source_server, target_server, instance_uid, debug=False):
        """
        Request an image from one PACS Orthanc instance to another.
        """
        try:
            url = f"{source_server['rest_url']}/modalities/{target_server['ae_title']}/store"
            if debug:
                print(f"Requesting {instance_uid} from {source_server['ae_title']} to {target_server['ae_title']}")

            response = requests.post(url, json=[instance_uid], auth=("orthanc", "orthanc"))

            if response.ok:
                if debug:
                    print(f"Successfully retrieved {instance_uid} to {target_server['ae_title']}")
                return True
            else:
                if debug:
                    print(f"Failed to retrieve {instance_uid} - HTTP {response.status_code}")
                return False

        except requests.RequestException as e:
            if debug:
                print(f"Error retrieving {instance_uid}: {e}")
            return False

    def retrieve_from_probe(self, instance_uid, debug=False):
        """
        Request an image from the probe server.
        """
        try:
            url = f"{self.probe_server['rest_url']}/instances/{instance_uid}/file"
            if debug:
                print(f"Retrieving {instance_uid} from {self.probe_server['ae_title']}")

            response = requests.get(url, auth=("orthanc", "orthanc"))

            if response.ok:
                if debug:
                    print(f"Successfully retrieved {instance_uid} from {self.probe_server['ae_title']}")
                return response.content  # Returns the binary DICOM file
            else:
                if debug:
                    print(f"Failed to retrieve {instance_uid} - HTTP {response.status_code}")
                return None

        except requests.RequestException as e:
            if debug:
                print(f"Error retrieving {instance_uid}: {e}")
            return None
