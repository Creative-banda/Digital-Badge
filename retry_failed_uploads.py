#!/usr/bin/python3
# -*- coding: UTF-8 -*-
"""
Retry Failed Uploads Script
----------------------------
This script retries all failed Google Sheets uploads stored in failed_uploads/

Usage:
    python retry_failed_uploads.py
"""

import json
import requests
import base64
import os
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

BACKUP_JSON = "failed_uploads/pending_uploads.json"
GOOGLE_APPS_SCRIPT_URL = os.getenv("GOOGLE_APPS_SCRIPT_URL", "")

def encode_image_to_base64(image_path):
    """Encode image file to base64 string"""
    try:
        with open(image_path, "rb") as f:
            return base64.b64encode(f.read()).decode()
    except Exception as e:
        print(f"Failed to encode {image_path}: {e}")
        return None

def retry_failed_uploads():
    """Retry all pending uploads from the backup JSON"""
    
    if not os.path.exists(BACKUP_JSON):
        print("✅ No failed uploads found! All good.")
        return
    
    if not GOOGLE_APPS_SCRIPT_URL:
        print("❌ Error: GOOGLE_APPS_SCRIPT_URL not set in .env file!")
        return
    
    # Load failed uploads
    with open(BACKUP_JSON, 'r') as f:
        failed_uploads = json.load(f)
    
    if not failed_uploads:
        print("✅ No pending uploads found!")
        return
    
    print(f"📋 Found {len(failed_uploads)} pending upload(s)")
    print("=" * 50)
    
    successful_uploads = []
    still_failed = []
    
    for idx, entry in enumerate(failed_uploads):
        if entry.get("status") != "pending":
            continue
        
        print(f"\n[{idx + 1}/{len(failed_uploads)}] Retrying: {entry['name']} at {entry['time']}")
        
        try:
            # Encode images
            current_image_b64 = encode_image_to_base64(entry['current_image_path'])
            known_face_b64 = encode_image_to_base64(entry['known_face_path'])
            
            if not current_image_b64 or not known_face_b64:
                print("  ❌ Failed to encode images")
                still_failed.append(entry)
                continue
            
            # Prepare data
            data = {
                "name": entry['name'],
                "time": entry['time'],
                "user_current_image": current_image_b64,
                "user_badge_image": known_face_b64
            }
            
            # Send to Google Sheets
            print(f"  🔄 Uploading...")
            response = requests.post(GOOGLE_APPS_SCRIPT_URL, json=data, timeout=30)
            
            if response.status_code == 200:
                print(f"  ✅ Success!")
                entry['status'] = 'uploaded'
                entry['uploaded_at'] = datetime.now().isoformat()
                successful_uploads.append(entry)
                
                # Clean up images
                try:
                    os.remove(entry['current_image_path'])
                    os.remove(entry['known_face_path'])
                    print(f"  🗑️  Cleaned up backup images")
                except:
                    pass
            else:
                print(f"  ❌ Failed: HTTP {response.status_code}")
                still_failed.append(entry)
                
        except Exception as e:
            print(f"  ❌ Error: {e}")
            still_failed.append(entry)
    
    print("\n" + "=" * 50)
    print(f"📊 Summary:")
    print(f"  ✅ Successful: {len(successful_uploads)}")
    print(f"  ❌ Still Failed: {len(still_failed)}")
    
    # Update JSON with results
    if still_failed:
        with open(BACKUP_JSON, 'w') as f:
            json.dump(still_failed, f, indent=2)
        print(f"\n💾 {len(still_failed)} failed upload(s) saved for next retry")
    else:
        # All successful - delete JSON file
        os.remove(BACKUP_JSON)
        print("\n🎉 All uploads successful! Backup file deleted.")
        
        # Try to remove empty backup directory
        try:
            if os.path.exists("failed_uploads/images"):
                os.rmdir("failed_uploads/images")
            os.rmdir("failed_uploads")
            print("🗑️  Removed empty backup directory")
        except:
            pass

if __name__ == "__main__":
    print("🔄 Retrying Failed Google Sheets Uploads")
    print("=" * 50)
    retry_failed_uploads()
