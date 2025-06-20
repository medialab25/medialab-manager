#!/usr/bin/env python3
"""Script to send a test event with text attachment to the API"""

import requests
import json
import os

# Test configuration
BASE_URL = "http://localhost:4801"
EVENT_ENDPOINT = f"{BASE_URL}/api/events/add_event"

def send_test_with_attachment():
    """Send a test event with a text file attachment"""
    print("📤 Sending test event with text attachment...")
    
    # Create a test text file with some interesting content
    test_file_content = """Test Log File
================

This is a sample log file for testing the attachment functionality.

System Information:
- OS: Linux 6.1.0-35-amd64
- Python: 3.x
- Application: MediaLab Manager

Recent Events:
2025-06-20 16:05:27 - Event created successfully
2025-06-20 16:05:28 - Attachment uploaded
2025-06-20 16:05:29 - Test completed

Configuration:
- Database: SQLite
- API Port: 4801
- Debug Mode: False

This attachment demonstrates how the system handles text files
and can be used to test the UI attachment viewing functionality.
"""
    
    test_file_path = "test_log.txt"
    
    with open(test_file_path, 'w') as f:
        f.write(test_file_content)
    
    try:
        with open(test_file_path, 'rb') as f:
            files = {'attachment': ('test_log.txt', f, 'text/plain')}
            
            data = {
                'type': 'test',
                'sub_type': 'ui_test',
                'status': 'success',
                'description': 'Test event with text attachment for UI testing',
                'details': json.dumps({
                    'test_data': 'This is a test event with text file attachment',
                    'source': 'ui_test_script',
                    'file_type': 'text/plain',
                    'file_name': 'test_log.txt',
                    'purpose': 'UI attachment testing'
                })
            }
            
            response = requests.post(EVENT_ENDPOINT, data=data, files=files)
            print(f"Status Code: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                print("✅ Success: Event created with text attachment")
                print(f"Event ID: {result['id']}")
                print(f"Event Type: {result['type']}")
                print(f"Description: {result['description']}")
                print(f"Has Attachment: {result['has_attachment']}")
                print(f"\nYou can now view this event in the UI at:")
                print(f"{BASE_URL}/events")
                print(f"Or view the attachment directly at:")
                print(f"{BASE_URL}/api/events/{result['id']}/attachment")
                return result['id']
            else:
                print("❌ Failed: Could not create event with attachment")
                print(f"Response: {response.text}")
                return None
                
    except Exception as e:
        print(f"❌ Error: {e}")
        return None
    finally:
        # Clean up test file
        if os.path.exists(test_file_path):
            os.remove(test_file_path)

def send_test_with_json_attachment():
    """Send a test event with a JSON file attachment"""
    print("\n📤 Sending test event with JSON attachment...")
    
    # Create a test JSON file
    test_json_data = {
        "test_config": {
            "name": "UI Test Configuration",
            "version": "1.0.0",
            "description": "Test configuration for UI attachment testing"
        },
        "settings": {
            "debug": False,
            "log_level": "INFO",
            "max_file_size": "10MB"
        },
        "features": [
            "text_attachment_viewing",
            "json_attachment_parsing",
            "file_download"
        ],
        "metadata": {
            "created_by": "test_script",
            "created_at": "2025-06-20T16:05:30",
            "purpose": "UI testing"
        }
    }
    
    test_file_path = "test_config.json"
    
    with open(test_file_path, 'w') as f:
        json.dump(test_json_data, f, indent=2)
    
    try:
        with open(test_file_path, 'rb') as f:
            files = {'attachment': ('test_config.json', f, 'application/json')}
            
            data = {
                'type': 'test',
                'sub_type': 'ui_test_json',
                'status': 'success',
                'description': 'Test event with JSON attachment for UI testing',
                'details': json.dumps({
                    'test_data': 'This is a test event with JSON file attachment',
                    'source': 'ui_test_script',
                    'file_type': 'application/json',
                    'file_name': 'test_config.json',
                    'purpose': 'UI JSON attachment testing'
                })
            }
            
            response = requests.post(EVENT_ENDPOINT, data=data, files=files)
            print(f"Status Code: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                print("✅ Success: Event created with JSON attachment")
                print(f"Event ID: {result['id']}")
                print(f"Event Type: {result['type']}")
                print(f"Description: {result['description']}")
                print(f"Has Attachment: {result['has_attachment']}")
                print(f"\nYou can now view this event in the UI at:")
                print(f"{BASE_URL}/events")
                print(f"Or view the attachment directly at:")
                print(f"{BASE_URL}/api/events/{result['id']}/attachment")
                return result['id']
            else:
                print("❌ Failed: Could not create event with JSON attachment")
                print(f"Response: {response.text}")
                return None
                
    except Exception as e:
        print(f"❌ Error: {e}")
        return None
    finally:
        # Clean up test file
        if os.path.exists(test_file_path):
            os.remove(test_file_path)

def main():
    """Run the test attachment scripts"""
    print("🚀 Starting UI attachment test...\n")
    
    # Send test with text attachment
    event_id_1 = send_test_with_attachment()
    
    # Send test with JSON attachment
    event_id_2 = send_test_with_json_attachment()
    
    print(f"\n🏁 Test completed!")
    if event_id_1:
        print(f"Text attachment event ID: {event_id_1}")
    if event_id_2:
        print(f"JSON attachment event ID: {event_id_2}")
    
    print(f"\nVisit {BASE_URL}/events to see the events in the UI")

if __name__ == "__main__":
    main() 