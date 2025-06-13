import os
import json

files_to_push = []

# Main files
main_files = ['README.md', 'LICENSE', 'QUICK_REFERENCE.md']
for f in main_files:
    if os.path.exists(f):
        with open(f, 'r') as file:
            content = file.read()
            files_to_push.append({
                'path': f,
                'content': content
            })

# Motion vector scripts
for root, dirs, files in os.walk('motion-vectors'):
    for file in files:
        if file.endswith(('.py', '.sh')):
            filepath = os.path.join(root, file)
            with open(filepath, 'r') as f:
                content = f.read()
                files_to_push.append({
                    'path': filepath,
                    'content': content
                })

# ASCII art scripts (sample - first 10)
count = 0
for root, dirs, files in os.walk('ascii-art'):
    for file in files:
        if file.endswith(('.py', '.sh')) and count < 10:
            filepath = os.path.join(root, file)
            with open(filepath, 'r') as f:
                content = f.read()
                files_to_push.append({
                    'path': filepath,
                    'content': content
                })
                count += 1

print(f"Total files to push: {len(files_to_push)}")
print("Files:", [f['path'] for f in files_to_push])

# Save for inspection
with open('/tmp/files_batch1.json', 'w') as f:
    json.dump(files_to_push[:20], f)  # First 20 files
