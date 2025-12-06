from datetime import datetime, timedelta
from django.conf import settings
import logging
import requests
from django.core.mail import EmailMultiAlternatives


logger = logging.getLogger(__name__)




def create_nocodeapi_event(appointment):
    """
    Create a Google Calendar event using NoCodeAPI
    """
    print("="*50)
    print("CREATING CALENDAR EVENT")
    print("="*50)
    print(f"Appointment Details: {appointment.__dict__}")

    try:
        url = f"{settings.NOCODEAPI_BASE_URL}/event"
        print(f"API URL: {url}")

        start_datetime = datetime.combine(appointment.date, appointment.time)
        end_datetime = start_datetime + timedelta(minutes=30)
        print(f"Start DateTime: {start_datetime}")
        print(f"End DateTime: {end_datetime}")

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
            "start": {"dateTime": start_datetime.isoformat(), "timeZone": "Asia/Kolkata"},
            "end": {"dateTime": end_datetime.isoformat(), "timeZone": "Asia/Kolkata"},
            "attendees": [
                {"email": appointment.email},
                {"email": appointment.doctor_email}
            ],
        }

        headers = {"Content-Type": "application/json"}
        print("Sending API Request with payload:")
        print(payload)
        logger.info(f"Sending calendar request to: {url}")

        response = requests.post(url, json=payload, headers=headers, timeout=10)

        print(f"API Response Status: {response.status_code}")
        print(f"Response Body: {response.text}")
        logger.info(f"Response: {response.status_code} - {response.text}")

        if response.status_code in [200, 201]:
            print("Calendar event created successfully")
            return response.json()
        else:
            response.raise_for_status()

    except requests.exceptions.RequestException as e:
        print(f"Request error: {e}")
        logger.error(f"Request failed: {e}")
        raise Exception(f"Calendar API request failed: {e}")
    except Exception as e:
        print(f"Unexpected error: {e}")
        logger.error(f"Unexpected error: {e}")
        raise Exception(f"An unexpected error occurred: {e}")   



