# test_nocodeapi.py - Run this as a standalone script to test your API
import requests
from datetime import datetime, timedelta

# Your NoCodeAPI URL
NOCODEAPI_BASE_URL = "https://v1.nocodeapi.com/nikhilchandurkar24/calendar/rOPZYmPKngwyeWba"

def test_calendar_api(): 
    url = f"{NOCODEAPI_BASE_URL}/event"
    
    # Test data
    start_time = datetime.now() + timedelta(days=1)  
    end_time = start_time + timedelta(minutes=30)
    
    payload = {
        "summary": "Test Appointment",
        "description": "This is a test appointment",
        "start": {
            "dateTime": start_time.isoformat(),
            "timeZone": "Asia/Kolkata"
        },
        "end": {
            "dateTime": end_time.isoformat(),
            "timeZone": "Asia/Kolkata"
        },
        "attendees": [
            {"email": "nikhilchandurkar24@gmail.com"},
            {"email": "nikhilchandurkar125@gmail.com"}
        ]
    }
    
    headers = {
        "Content-Type": "application/json"
    }
    
    try:
        print(f"Testing URL: {url}")
        print(f"Payload: {payload}")
        
        response = requests.post(url, json=payload, headers=headers, timeout=10)
        
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text}")
        
        if response.status_code == 200 or response.status_code == 201:
            print("✅ SUCCESS: Calendar API is working!")
        else:
            print("❌ FAILED: Check your API key and permissions")
            
    except Exception as e:
        print(f"❌ ERROR: {e}")

if __name__ == "__main__":
    test_calendar_api()