import os
import json
import cv2
from pathlib import Path

def prepare_metadata(video_dir, output_meta_path, default_prompt="A professional data insight visualization video"):
    """
    Scans a directory of videos and generates a metadata.json for Wan2.1 fine-tuning.
    """
    video_dir = Path(video_dir)
    metadata = []

    if not video_dir.exists():
        print(f"Error: {video_dir} does not exist. Please create it and add your .mp4 clips.")
        return

    # Supported video formats
    extensions = {".mp4", ".mkv", ".mov", ".avi"}
    
    print(f"Scanning {video_dir} for video files...")
    
    video_files = [f for f in video_dir.iterdir() if f.suffix.lower() in extensions]
    
    for video_file in video_files:
        try:
            # Open video to get dimensions
            cap = cv2.VideoCapture(str(video_file))
            if not cap.isOpened():
                print(f"Could not open {video_file}, skipping.")
                continue
                
            width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            cap.release()

            # Clean filename for prompt if no external caption file exists
            # In a real scenario, you'd load captions from a .txt file with the same name
            caption_file = video_file.with_suffix(".txt")
            if caption_file.exists():
                text = caption_file.read_text(encoding="utf-8").strip()
            else:
                text = default_prompt

            entry = {
                "file_path": f"train/{video_file.name}",
                "text": text,
                "type": "video",
                "width": width,
                "height": height
            }
            metadata.append(entry)
            print(f"Added {video_file.name} ({width}x{height})")
            
        except Exception as e:
            print(f"Error processing {video_file}: {e}")

    # Save metadata.json
    os.makedirs(os.path.dirname(output_meta_path), exist_ok=True)
    with open(output_meta_path, "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2)
    
    print(f"\nMetadata generation complete. Saved to: {output_meta_path}")
    print(f"Total videos processed: {len(metadata)}")

if __name__ == "__main__":
    # Configure paths
    TRAIN_DIR = "./training_videos"
    OUTPUT_META = "./datasets/my_custom_dataset/metadata.json"
    
    prepare_metadata(TRAIN_DIR, OUTPUT_META)
