import zipfile
import shutil
import os

# Test reading and re-packing a docx file
source_file = 'update4.docx'
test_file = 'scratch/test_roundtrip.docx'

with zipfile.ZipFile(source_file, 'r') as zin:
    with zipfile.ZipFile(test_file, 'w', compression=zipfile.ZIP_DEFLATED) as zout:
        for item in zin.infolist():
            data = zin.read(item.filename)
            zout.writestr(item, data)

print(f"Original size: {os.path.getsize(source_file)}")
print(f"Roundtrip size: {os.path.getsize(test_file)}")
print("Roundtrip test successful!")
