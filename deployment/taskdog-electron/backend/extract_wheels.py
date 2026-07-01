import os
import sys
import zipfile
import shutil
import re

cache_dir = "/Users/sameerhoda/Library/Caches/pip"
out_dir = "/Users/sameerhoda/CRED/daily_brief/whatsapp_followup/task_dog_v1/.wheels"
os.makedirs(out_dir, exist_ok=True)

print(f"Scanning {cache_dir} for cached wheels...")

wheel_count = 0
for root, dirs, files in os.walk(cache_dir):
    for file in files:
        filepath = os.path.join(root, file)
        # Skip small files
        if os.path.getsize(filepath) < 1000:
            continue
        try:
            with open(filepath, 'rb') as f:
                content = f.read(1024)
                idx = content.find(b'PK\x03\x04')
                if idx == -1:
                    continue
                
                # Copy the ZIP portion to a temp file to read it
                f.seek(idx)
                zip_data = f.read()
                
            temp_path = os.path.join(out_dir, "temp.zip")
            with open(temp_path, 'wb') as temp_f:
                temp_f.write(zip_data)
                # read the rest of the file
                with open(filepath, 'rb') as orig_f:
                    orig_f.seek(idx + len(zip_data))
                    shutil.copyfileobj(orig_f, temp_f)
            
            # Verify if it's a valid ZIP and find METADATA
            if zipfile.is_zipfile(temp_path):
                with zipfile.ZipFile(temp_path) as z:
                    metadata_path = None
                    for name in z.namelist():
                        if name.endswith('.dist-info/METADATA'):
                            metadata_path = name
                            break
                    
                    if metadata_path:
                        metadata_content = z.read(metadata_path).decode('utf-8', errors='ignore')
                        name_match = re.search(r'^Name:\s*(.+)$', metadata_content, re.MULTILINE)
                        version_match = re.search(r'^Version:\s*(.+)$', metadata_content, re.MULTILINE)
                        
                        if name_match and version_match:
                            pkg_name = name_match.group(1).strip()
                            pkg_version = version_match.group(1).strip()
                            # Clean name
                            pkg_name = re.sub(r'[^\w\d.]', '_', pkg_name)
                            pkg_version = re.sub(r'[^\w\d.]', '_', pkg_version)
                            
                            # Determine filename (approximate)
                            new_filename = f"{pkg_name}-{pkg_version}-py3-none-any.whl"
                            new_path = os.path.join(out_dir, new_filename)
                            
                            # Copy to final path
                            shutil.copy(temp_path, new_path)
                            print(f"Extracted: {new_filename}")
                            wheel_count += 1
            
            if os.path.exists(temp_path):
                os.remove(temp_path)
        except Exception as e:
            pass

print(f"Finished! Extracted {wheel_count} wheels to {out_dir}")
