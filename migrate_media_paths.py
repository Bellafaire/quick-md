#!/usr/bin/env python3
"""
Migrate old media paths in .qmd_conf to match actual directory structure.
Updates paths like 'images/file.png' to 'assets/file.png' if files are in assets directory.
"""

import os
import sys
from utils.configurations_manager import ConfigurationManager

def migrate_paths():
    cm = ConfigurationManager()
    
    md_path = cm.config['local']['md_path']
    images_path = cm.config['local']['images_path']
    videos_path = cm.config['local']['videos_path']
    
    # Calculate what the relative paths should be
    images_rel = os.path.relpath(images_path, md_path)
    videos_rel = os.path.relpath(videos_path, md_path)
    
    print("Current configuration:")
    print(f"  md_path: {md_path}")
    print(f"  images_path: {images_path}")
    print(f"  videos_path: {videos_path}")
    print(f"\nRelative paths should be:")
    print(f"  images: {images_rel}")
    print(f"  videos: {videos_rel}")
    print()
    
    # Migrate Images
    images_updated = 0
    if 'Images' in cm.config and cm.config['Images']:
        print(f"Found {len(cm.config['Images'])} image entries")
        new_images = []
        for img_path in cm.config['Images']:
            # Extract just the filename
            filename = os.path.basename(img_path)
            
            # Check if file exists in the configured images directory
            full_path = os.path.join(images_path, filename)
            if os.path.exists(full_path):
                # Build correct relative path
                new_path = f"{images_rel}/{filename}"
                if new_path != img_path:
                    print(f"  Migrating: {img_path} -> {new_path}")
                    images_updated += 1
                    new_images.append(new_path)
                else:
                    new_images.append(img_path)
            else:
                print(f"  Warning: File not found for {img_path}, keeping as-is")
                new_images.append(img_path)
        
        cm.config['Images'] = new_images
        cm.config_raw['Images'] = new_images
    
    # Migrate Videos
    videos_updated = 0
    if 'Videos' in cm.config and cm.config['Videos']:
        print(f"\nFound {len(cm.config['Videos'])} video entries")
        new_videos = []
        for vid_path in cm.config['Videos']:
            # Extract just the filename
            filename = os.path.basename(vid_path)
            
            # Check if file exists in the configured videos directory
            full_path = os.path.join(videos_path, filename)
            if os.path.exists(full_path):
                # Build correct relative path
                new_path = f"{videos_rel}/{filename}"
                if new_path != vid_path:
                    print(f"  Migrating: {vid_path} -> {new_path}")
                    videos_updated += 1
                    new_videos.append(new_path)
                else:
                    new_videos.append(vid_path)
            else:
                print(f"  Warning: File not found for {vid_path}, keeping as-is")
                new_videos.append(vid_path)
        
        cm.config['Videos'] = new_videos
        cm.config_raw['Videos'] = new_videos
    
    # Show summary
    print(f"\n{'='*60}")
    print(f"Summary:")
    print(f"  Images updated: {images_updated}")
    print(f"  Videos updated: {videos_updated}")
    print(f"{'='*60}")
    
    if images_updated > 0 or videos_updated > 0:
        print("\nReady to save changes to .qmd_conf")
        response = input("Save changes? (y/n): ").strip().lower()
        if response == 'y':
            cm.save_config()
            print("✓ Configuration updated successfully!")
            print("\nNext steps:")
            print("  1. Restart your web server (main.py)")
            print("  2. The 'Insert Media' button will now show correct paths")
            return 0
        else:
            print("Changes not saved.")
            return 1
    else:
        print("\nNo changes needed - paths are already correct!")
        return 0

if __name__ == "__main__":
    try:
        sys.exit(migrate_paths())
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
