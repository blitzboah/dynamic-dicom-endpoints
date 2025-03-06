import requests

ORTHANC_URLS = ["http://localhost:8042", "http://localhost:8052"]
AUTH = ("orthanc", "orthanc")

for url in ORTHANC_URLS:
    response = requests.get(f"{url}/instances", auth=AUTH)
    instances = response.json()

    for instance in instances:
        delete_url = f"{url}/instances/{instance}"
        delete_response = requests.delete(delete_url, auth=AUTH)
        print(f"Deleted {instance} from {url}: {delete_response.status_code}")

print("All images deleted from Orthanc instances!")