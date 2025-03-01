from orthanc_manager import OrthancManager

def route_dicom_image(ds):
    """
    Route the DICOM image to the least loaded Orthanc server.
    """
    import os
    print("Starting to route DICOM image...")
    
    orthanc_servers = [
        {'ae_title': 'ORTHANC1', 'host': 'localhost', 'port': 4242, 'rest_url': 'http://localhost:8042'},
        {'ae_title': 'ORTHANC2', 'host': 'localhost', 'port': 4243, 'rest_url': 'http://localhost:8043'}
    ]
    
    print(f"Configured servers: {[s['ae_title'] for s in orthanc_servers]}")
    
    orthanc_manager = OrthancManager(orthanc_servers)
    
    try:
        # find the least loaded server
        print("Checking server loads...")
        server_loads = {}
        available_servers = []
        
        for server in orthanc_servers:
            try:
                count = orthanc_manager.get_instance_count(server)
                if count != float('inf'):
                    server_loads[server['ae_title']] = count
                    available_servers.append(server)
                    print(f"Server {server['ae_title']} has {count} instances")
                else:
                    print(f"Server {server['ae_title']} is not available")
            except Exception as e:
                print(f"Error checking server {server['ae_title']}: {e}")
        
        if not available_servers:
            print("No available servers found!")
            return
            
        selected_server = min(available_servers, key=lambda s: orthanc_manager.get_instance_count(s))
        print(f"Selected server: {selected_server['ae_title']}")
        
        # save the DICOM dataset to a temporary file
        temp_file = f"/tmp/{ds.SOPInstanceUID}.dcm"
        print(f"Saving DICOM to temporary file: {temp_file}")
        ds.save_as(temp_file)
        
        # send the DICOM image to the selected server
        print(f"Attempting to send to {selected_server['ae_title']}...")
        success = orthanc_manager.send_dicom_image(selected_server, temp_file)
        
        # Clean up the temporary file
        try:
            os.remove(temp_file)
            print(f"Removed temporary file: {temp_file}")
        except OSError as e:
            print(f"Error removing temporary file: {e}")
            
        if success:
            print(f"Successfully sent DICOM image to {selected_server['ae_title']}")
        else:
            print(f"Failed to send DICOM image to {selected_server['ae_title']}")
            
    except Exception as e:
        print(f"Error in routing DICOM image: {e}")
