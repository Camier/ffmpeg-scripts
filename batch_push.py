#!/usr/bin/env python3
import os
import json
from pathlib import Path

def gather_files_for_push():
    """Gather all script files for pushing to GitHub"""
    files_to_push = []
    
    # Motion vector scripts
    for root, dirs, files in os.walk('motion-vectors'):
        for file in files:
            if file.endswith('.py'):
                filepath = os.path.join(root, file)
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        content = f.read()
                        files_to_push.append({
                            'path': filepath,
                            'content': content,
                            'size': len(content)
                        })
                        print(f"✓ Read {filepath} ({len(content)} bytes)")
                except Exception as e:
                    print(f"✗ Error reading {filepath}: {e}")
    
    # ASCII scripts - just get first 10 as examples
    ascii_count = 0
    for root, dirs, files in os.walk('ascii-art'):
        for file in sorted(files):
            if file.endswith(('.py', '.sh')) and ascii_count < 10:
                filepath = os.path.join(root, file)
                try:
                    with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read()
                        files_to_push.append({
                            'path': filepath,
                            'content': content,
                            'size': len(content)
                        })
                        print(f"✓ Read {filepath} ({len(content)} bytes)")
                        ascii_count += 1
                except Exception as e:
                    print(f"✗ Error reading {filepath}: {e}")
    
    # Save to batches for GitHub API limits
    batch_size = 10
    for i in range(0, len(files_to_push), batch_size):
        batch = files_to_push[i:i+batch_size]
        batch_file = f'/tmp/github_batch_{i//batch_size + 1}.json'
        with open(batch_file, 'w') as f:
            json.dump(batch, f)
        print(f"\nBatch {i//batch_size + 1} saved to {batch_file}")
        print(f"Files in batch: {[f['path'] for f in batch]}")
    
    print(f"\nTotal files prepared: {len(files_to_push)}")
    return len(files_to_push)

if __name__ == "__main__":
    gather_files_for_push()
