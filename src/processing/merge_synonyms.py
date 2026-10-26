import os
import shutil
from pathlib import Path

RAW_ROOT = Path('data/raw')
MERGE_MAP = {
    'IndianGooseberry': 'Amla',
    'MalabarNut': 'Adulsa',
    'Bringaraj': 'Bhringraj',
    'IndianPennywort': 'GotoKola'
}

def merge_folders():
    for source_dir in RAW_ROOT.iterdir():
        if not source_dir.is_dir() or source_dir.name == 'review':
            continue
            
        for old_name, new_name in MERGE_MAP.items():
            old_dir = source_dir / old_name
            new_dir = source_dir / new_name
            
            if old_dir.exists():
                print(f"Merging {old_dir} into {new_dir}")
                new_dir.mkdir(parents=True, exist_ok=True)
                
                for fpath in old_dir.iterdir():
                    if fpath.is_file():
                        dst_path = new_dir / fpath.name
                        if not dst_path.exists():
                            shutil.move(str(fpath), str(dst_path))
                        else:
                            # File already exists in the destination, we can safely delete the duplicate
                            fpath.unlink()
                            
                # Remove the old directory since it should now be empty
                try:
                    old_dir.rmdir()
                except OSError as e:
                    print(f"Could not remove {old_dir}: {e}")

if __name__ == '__main__':
    merge_folders()
    print("Done merging.")
