from flask import Flask, render_template, request, jsonify, redirect, url_for, flash
import os
import subprocess
import tempfile
import time
import threading
import requests
import socket
import urllib.parse
import pydicom
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = 'dynamic_dicom_endpoints_secret_key'

# Configuration
UPLOAD_FOLDER = 'temp_dicom_files'
ALLOWED_EXTENSIONS = {'dcm'}
DEFAULT_TARGET_AE = 'DYNAMIC_DICOM_MW'
DEFAULT_SOURCE_AE = 'TEST_SCU'

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 100 * 1024 * 1024  # 100 MB limit

os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# we can later use db or other source of urls to load it dyanmically instead of hardcoding
ORTHANC_SERVERS = [
    {"name": "Orthanc Storage 1", "dicom_host": "orthanc-storage-1", "dicom_port": 4242, "http_url": "http://orthanc-storage-1:8042"},
    {"name": "Orthanc Storage 2", "dicom_host": "orthanc-storage-2", "dicom_port": 4243, "http_url": "http://orthanc-storage-2:8043"},
    {"name": "Orthanc Probe", "dicom_host": "orthanc-probe", "dicom_port": 4252, "http_url": "http://orthanc-probe:8052"},
    {"name": "DICOM Middleware", "dicom_host": "dicom-middleware-cli", "dicom_port": 11113, "http_url": "http://dicom-middleware-cli:11113"}
]

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def send_dicom(filepath, source_ae, target_ae, host, port, retries=2):
    if target_ae == "DYNAMIC_DICOM_MW":
        try:
            from middleware import route_dicom_image
        except ImportError:
            return False, "Middleware module not available"
        # Read the DICOM file using pydicom
        ds = pydicom.dcmread(filepath)
        # Call middleware routing function
        ae_title, instance_count = route_dicom_image(ds, debug=True)
        if ae_title is not None:
            return ae_title, f"Instance count: {instance_count}"
        else:
            return False, "Middleware failed to route image"
    else:
        command = [
            'storescu',
            '-v',
            '-aet', source_ae,
            '-aec', target_ae,
            host,
            str(port),
            filepath
        ]
        print(f"Executing command: {' '.join(command)}")
        for attempt in range(retries + 1):
            try:
                result = subprocess.run(command, capture_output=True, text=True, check=True, timeout=10)
                return True, result.stdout
            except subprocess.CalledProcessError as e:
                error = e.stderr
                if attempt < retries:
                    print(f"Attempt {attempt+1} failed, retrying...")
                    time.sleep(1)
                else:
                    return False, error
            except subprocess.TimeoutExpired:
                if attempt < retries:
                    print(f"Timeout on attempt {attempt+1}, retrying...")
                    time.sleep(1)
                else:
                    return False, "Command timed out after 10 seconds"

def get_server_load(server):
    """Fetch the load of an Orthanc server (e.g., number of studies)"""
    try:
        response = requests.get(f"{server['http_url']}/system", auth=("orthanc", "orthanc"), timeout=2)
        if response.status_code == 200:
            stats = requests.get(f"{server['http_url']}/statistics", auth=("orthanc", "orthanc"), timeout=2).json()
            return {
                "name": server["name"],
                "dicom_host": server["dicom_host"],
                "dicom_port": server["dicom_port"],
                "instances": stats.get("CountInstances", 0),
                "online": True
            }
        else:
            return {
                "name": server["name"],
                "dicom_host": server["dicom_host"],
                "dicom_port": server["dicom_port"],
                "instances": stats.get("CountInstances", 0),
                "online": False
            }
    except requests.RequestException:
        return {
            "name": server["name"],
            "dicom_host": server["dicom_host"],
            "dicom_port": server["dicom_port"],
            "instances": stats.get("CountInstances", 0),
            "online": False
        }

def find_least_loaded_server():
    """Find the least loaded Orthanc server based on the number of instances"""

    storage_servers = [server for server in ORTHANC_SERVERS if "middleware" not in server["name"].lower()]
    server_loads = [get_server_load(server) for server in storage_servers]
    online_servers = [server for server in server_loads if server["online"]]

    if not online_servers:
        raise Exception("No Orthanc servers are online")

    least_loaded = min(online_servers, key=lambda x: x["instances"])
    return least_loaded["dicom_host"], least_loaded["dicom_port"]

def remove_old_files():
    """Background task to remove files older than 1 hour"""
    while True:
        now = time.time()
        for filename in os.listdir(app.config['UPLOAD_FOLDER']):
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            if os.path.isfile(filepath) and os.path.getmtime(filepath) < now - 3600:
                os.remove(filepath)
        time.sleep(3600)  # Check every hour

cleanup_thread = threading.Thread(target=remove_old_files, daemon=True)
cleanup_thread.start()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'dicomFile' not in request.files:
        flash('No file part')
        return redirect(request.url)
    
    file = request.files['dicomFile']
    if file.filename == '':
        flash('No selected file')
        return redirect(request.url)
    
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        
        source_ae = request.form.get('sourceAE', DEFAULT_SOURCE_AE)
        target_ae = request.form.get('targetAE', DEFAULT_TARGET_AE)
        
        try:
            # Dynamically find the least loaded server
            host, port = find_least_loaded_server()
        except Exception as e:
            flash(str(e), 'error')
            return redirect(url_for('index'))
        
        host = request.form.get('host', host)
        port = request.form.get('port', port)

        if target_ae == "DYNAMIC_DICOM_MW":
            host = "dicom-middleware-cli"
            port = 11113
        else:
            host, port = find_least_loaded_server()

        
        print(f"Using source_ae: {source_ae}, target_ae: {target_ae}, host: {host}, port: {port}")  # Debugging
        result = send_dicom(filepath, source_ae, target_ae, host, port)

        if isinstance(result, tuple):
            selected_orthanc, message = result
        else:
            selected_orthanc = None
            message = result

        if selected_orthanc:
            flash(f'Successfully sent {filename} to {selected_orthanc}', 'success')
        else:
            flash(f'Failed to send {filename}: {message}', 'error')

            
        return redirect(url_for('index'))
    
    flash('Invalid file type. Only DCM files are allowed.')
    return redirect(url_for('index'))

@app.route('/servers')
def server_status():
    """Returns the status of the Orthanc servers with complete information"""
    servers_data = []
    
    for server in ORTHANC_SERVERS:
        if "middleware" in server["name"].lower():
            continue  # Skip middleware
        servers_data.append({
            "name": server["name"],
            "url": server["http_url"],
            "dicom_host": server["dicom_host"],
            "dicom_port": server["dicom_port"]
        })

        
    return render_template('servers.html', servers=servers_data)

@app.route('/api/check_server', methods=['POST'])
def check_server():
    """API endpoint to check if a server is online with improved error handling"""
    data = request.json
    url = data.get('url')
    
    try:
        # First do a basic connection test with a short timeout
        parsed_url = urllib.parse.urlparse(url)
        host = parsed_url.hostname
        port = parsed_url.port or (443 if parsed_url.scheme == 'https' else 80)
        
        # Test basic network connectivity first
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(1)
        
        connection_result = sock.connect_ex((host, port))
        sock.close()
        
        if connection_result != 0:
            return jsonify({
                "status": "offline", 
                "message": f"Cannot connect to {host}:{port}. Check firewall or network settings.",
                "connection_error": connection_result
            })

        response = requests.get(f"{url}/system", auth=("orthanc", "orthanc"), timeout=5)
        if response.status_code == 200:
            stats = requests.get(f"{url}/statistics", auth=("orthanc", "orthanc"), timeout=5).json()
            return jsonify({
                "status": "online",
                "name": response.json().get("Name", "Unknown"),
                "version": response.json().get("Version", "Unknown"),
                "patients": stats.get("CountPatients", 0),
                "studies": stats.get("CountStudies", 0),
                "instances": stats.get("CountInstances", 0),
                "uptime": response.json().get("UptimeInSeconds", 0),
                "dicom_port": data.get("dicom_port", "N/A"),
                "host_address": host
            })
        else:
            return jsonify({
                "status": "error", 
                "message": f"Server returned status code {response.status_code}",
                "http_status": response.status_code
            })
            
    except requests.RequestException as e:
        return jsonify({
            "status": "offline", 
            "message": str(e),
            "host": host,
            "port": port
        })
    except Exception as e:
        return jsonify({
            "status": "error", 
            "message": f"Unexpected error: {str(e)}",
            "error_type": type(e).__name__
        })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)