import requests
from datetime import datetime, timedelta
from django.conf import settings
import logging

logger = logging.getLogger(__name__)

def create_nocodeapi_event(appointment):
    """
    Create a Google Calendar event using NoCodeAPI
    """
    print(f"\n{'='*50}")
    print(f"🔄 CREATING CALENDAR EVENT")
    print(f"{'='*50}")
    print(f"📋 Appointment Details:")
    print(f"   - Service: {appointment.service}")
    print(f"   - Patient: {appointment.name}")
    print(f"   - Patient Email: {appointment.email}")
    print(f"   - Doctor Email: {appointment.doctor_email}")
    print(f"   - Date: {appointment.date}")
    print(f"   - Time: {appointment.time}")
    print(f"   - Message: {appointment.message or 'None'}")
    
    try:
        url = f"{settings.NOCODEAPI_BASE_URL}/event"
        print(f"\n🌐 API URL: {url}")
        
        # Combine date and time
        start_datetime = datetime.combine(appointment.date, appointment.time)
        end_datetime = start_datetime + timedelta(minutes=30)
        
        print(f"⏰ Start DateTime: {start_datetime}")
        print(f"⏰ End DateTime: {end_datetime}")
        
        payload = {
            "summary": f"Dental Appointment: {appointment.service}",
            "description": f"""
Appointment Details:
- Service: {appointment.service}
- Patient: {appointment.name}
- Patient Email: {appointment.email}
- Doctor: {appointment.doctor_email}
- Additional Notes: {appointment.message or "None"}
            """.strip(),
            "start": {
                "dateTime": start_datetime.isoformat(),
                "timeZone": "Asia/Kolkata"
            },
            "end": {
                "dateTime": end_datetime.isoformat(),
                "timeZone": "Asia/Kolkata"
            },
            "attendees": [
                {"email": appointment.email},
                {"email": appointment.doctor_email}
            ],
        }

        headers = {
            "Content-Type": "application/json"
        }

        print(f"\n📤 Sending API Request:")
        print(f"Headers: {headers}")
        print(f"Payload: {payload}")
        
        logger.info(f"Sending calendar request to: {url}")
        logger.info(f"Payload: {payload}")

        response = requests.post(url, json=payload, headers=headers, timeout=10)
        
        print(f"\n📥 API Response:")
        print(f"Status Code: {response.status_code}")
        print(f"Response Headers: {dict(response.headers)}")
        print(f"Response Body: {response.text}")
        
        logger.info(f"Response status: {response.status_code}")
        logger.info(f"Response body: {response.text}")

        if response.status_code in [200, 201]:
            print(f"✅ SUCCESS: Calendar event created successfully!")
            return response.json()
        else:
            print(f"❌ FAILED: API returned status {response.status_code}")
            response.raise_for_status()

    except requests.exceptions.RequestException as e:
        print(f"❌ REQUEST ERROR: {e}")
        logger.error(f"Request failed: {e}")
        raise Exception(f"Calendar API request failed: {e}")
    except Exception as e:
        print(f"❌ UNEXPECTED ERROR: {e}")
        logger.error(f"Unexpected error: {e}")
        raise