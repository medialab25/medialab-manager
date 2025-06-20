#!/usr/bin/env python3
"""Test script for the add_event endpoint"""

import requests
import json
import os

# Test configuration
BASE_URL = "http://localhost:4801"
EVENT_ENDPOINT = f"{BASE_URL}/api/events/add_event"

def test_add_event_without_attachment():
    """Test adding an event without file attachment"""
    print("Testing add_event without attachment...")
    
    data = {
        'type': 'test',
        'sub_type': 'api_test',
        'status': 'success',
        'description': 'Test event from API',
        'details': json.dumps({'test_data': 'This is a test event', 'source': 'api_test'})
    }
    
    try:
        response = requests.post(EVENT_ENDPOINT, data=data)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.json()}")
        
        if response.status_code == 200:
            print("✅ Success: Event created without attachment")
            return response.json()['id']
        else:
            print("❌ Failed: Could not create event")
            return None
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return None

def test_add_event_with_attachment():
    """Test adding an event with file attachment"""
    print("\nTesting add_event with attachment...")
    
    # Create a test file
    test_file_content = "This is a test file attachment\nCreated for API testing"
    test_file_path = "test_attachment.txt"
    
    with open(test_file_path, 'w') as f:
        f.write(test_file_content)
    
    try:
        with open(test_file_path, 'rb') as f:
            files = {'attachment': ('test_attachment.txt', f, 'text/plain')}
            
            data = {
                'type': 'test',
                'sub_type': 'api_test_with_file',
                'status': 'success',
                'description': 'Test event with file attachment',
                'details': json.dumps({'test_data': 'This is a test event with file', 'source': 'api_test'})
            }
            
            response = requests.post(EVENT_ENDPOINT, data=data, files=files)
            print(f"Status Code: {response.status_code}")
            print(f"Response: {response.json()}")
            
            if response.status_code == 200:
                print("✅ Success: Event created with attachment")
                return response.json()['id']
            else:
                print("❌ Failed: Could not create event with attachment")
                return None
                
    except Exception as e:
        print(f"❌ Error: {e}")
        return None
    finally:
        # Clean up test file
        if os.path.exists(test_file_path):
            os.remove(test_file_path)

def test_add_event_with_custom_attachment_type():
    """Test adding an event with custom attachment type"""
    print("\nTesting add_event with custom attachment_type...")
    
    # Create a test file
    test_file_content = "This is a test file attachment\nCreated for API testing with custom type"
    test_file_path = "test_attachment_custom.txt"
    
    with open(test_file_path, 'w') as f:
        f.write(test_file_content)
    
    try:
        with open(test_file_path, 'rb') as f:
            files = {'attachment': ('test_attachment_custom.txt', f, 'text/plain')}
            
            data = {
                'type': 'test',
                'sub_type': 'api_test_custom_type',
                'status': 'success',
                'description': 'Test event with custom attachment type',
                'details': json.dumps({'test_data': 'This is a test event with custom type', 'source': 'api_test'}),
                'attachment_type': 'application/custom-type'  # Custom MIME type
            }
            
            response = requests.post(EVENT_ENDPOINT, data=data, files=files)
            print(f"Status Code: {response.status_code}")
            print(f"Response: {response.json()}")
            
            if response.status_code == 200:
                print("✅ Success: Event created with custom attachment type")
                return response.json()['id']
            else:
                print("❌ Failed: Could not create event with custom attachment type")
                return None
                
    except Exception as e:
        print(f"❌ Error: {e}")
        return None
    finally:
        # Clean up test file
        if os.path.exists(test_file_path):
            os.remove(test_file_path)

def test_get_event(event_id):
    """Test retrieving the created event"""
    if not event_id:
        return
        
    print(f"\nTesting get_event for ID {event_id}...")
    
    try:
        response = requests.get(f"{BASE_URL}/api/events/{event_id}")
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            event = response.json()
            print("✅ Success: Retrieved event")
            print(f"Event Type: {event['type']}")
            print(f"Event Description: {event['description']}")
            print(f"Has Attachment: {event['has_attachment']}")
            return event
        else:
            print("❌ Failed: Could not retrieve event")
            return None
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return None

def test_get_attachment(event_id):
    """Test retrieving the attachment if it exists"""
    if not event_id:
        return
        
    print(f"\nTesting get_event_attachment for ID {event_id}...")
    
    try:
        response = requests.get(f"{BASE_URL}/api/events/{event_id}/attachment")
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            print("✅ Success: Retrieved attachment")
            print(f"Content Type: {response.headers.get('content-type', 'unknown')}")
            print(f"Content Length: {len(response.content)} bytes")
            return response.content
        elif response.status_code == 404:
            print("ℹ️  No attachment found (expected for events without attachments)")
            return None
        else:
            print("❌ Failed: Could not retrieve attachment")
            return None
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return None

def main():
    """Run all tests"""
    print("🚀 Starting add_event endpoint tests...\n")
    
    # Test 1: Event without attachment
    event_id_1 = test_add_event_without_attachment()
    if event_id_1:
        test_get_event(event_id_1)
        test_get_attachment(event_id_1)
    
    # Test 2: Event with attachment
    event_id_2 = test_add_event_with_attachment()
    if event_id_2:
        test_get_event(event_id_2)
        attachment_content = test_get_attachment(event_id_2)
        if attachment_content:
            print(f"Attachment content: {attachment_content.decode('utf-8')}")
    
    # Test 3: Event with custom attachment type
    event_id_3 = test_add_event_with_custom_attachment_type()
    if event_id_3:
        test_get_event(event_id_3)
        attachment_content = test_get_attachment(event_id_3)
        if attachment_content:
            print(f"Attachment content: {attachment_content.decode('utf-8')}")
    
    print("\n🏁 Tests completed!")

if __name__ == "__main__":
    main() 