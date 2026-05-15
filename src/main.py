import os
import sys
import json

def create_structure(base, depth):
    if depth <= 0: return
    for i in range(2):
        new_path = os.path.join(base, f'node_{depth}_{i}')
        os.makedirs(new_path, exist_ok=True)
        with open(os.path.join(new_path, 'metadata.json'), 'w') as f:
            json.dump({'depth': depth