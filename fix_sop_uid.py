import pydicom

dicom_files = ["dcm_files/test_file1.dcm", "dcm_files/test_file2.dcm", "dcm_files/test_file3.dcm", "dcm_files/test_file4.dcm", "dcm_files/test_file5.dcm"]

for file in dicom_files:
    ds = pydicom.dcmread(file, force=True)

    if "SOPClassUID" not in ds:
        ds.SOPClassUID = "1.2.840.10008.5.1.4.1.1.2"
        print(f"🛠️ Fixed SOPClassUID for {file}")

    ds.SOPInstanceUID = pydicom.uid.generate_uid()

    ds.save_as(file)
    print(f"Saved updated {file}")

print("All files updated!")
