from datetime import datetime, timedelta
from django.conf import settings
import logging
import requests
from django.core.mail import EmailMultiAlternatives


logger = logging.getLogger(__name__)

# def create_nocodeapi_event(appointment):
#     """
#     Create a Google Calendar event using NoCodeAPI
#     """
#     print(f"\n{'='*50}")
#     print(f" CREATING CALENDAR EVENT")
#     print(f"{'='*50}")
#     print(f" Appointment Details:")
#     print(f"   - Service: {appointment.service}")
#     print(f"   - Patient: {appointment.name}")
#     print(f"   - Patient Email: {appointment.email}")
#     print(f"   - Doctor Email: {appointment.doctor_email}")
#     print(f"   - Date: {appointment.date}")
#     print(f"   - Time: {appointment.time}")
#     print(f"   - Message: {appointment.message or 'None'}")
    
#     try:
#         url = f"{settings.NOCODEAPI_BASE_URL}/event"
#         print(f"\n🌐 API URL: {url}")
        
#         # Combine date and time
#         start_datetime = datetime.combine(appointment.date, appointment.time)
#         end_datetime = start_datetime + timedelta(minutes=30)
        
#         print(f"⏰ Start DateTime: {start_datetime}")
#         print(f"⏰ End DateTime: {end_datetime}")
        
#         payload = {
#             "summary": f"Dental Appointment: {appointment.service}",
#             "description": f"""
# Appointment Details:
# - Service: {appointment.service}
# - Patient: {appointment.name}
# - Patient Email: {appointment.email}
# - Doctor: {appointment.doctor_email}
# - Additional Notes: {appointment.message or "None"}
#             """.strip(),
#             "start": {
#                 "dateTime": start_datetime.isoformat(),
#                 "timeZone": "Asia/Kolkata"
#             },
#             "end": {
#                 "dateTime": end_datetime.isoformat(),
#                 "timeZone": "Asia/Kolkata"
#             },
#             "attendees": [
#                 {"email": appointment.email},
#                 {"email": appointment.doctor_email}
#             ],
#         }

#         headers = {
#             "Content-Type": "application/json"
#         }

#         print(f"\n📤 Sending API Request:")
#         print(f"Headers: {headers}")
#         print(f"Payload: {payload}")
        
#         logger.info(f"Sending calendar request to: {url}")
#         logger.info(f"Payload: {payload}")

#         response = requests.post(url, json=payload, headers=headers, timeout=10)
        
#         print(f"\n📥 API Response:")
#         print(f"Status Code: {response.status_code}")
#         print(f"Response Headers: {dict(response.headers)}")
#         print(f"Response Body: {response.text}")
        
#         logger.info(f"Response status: {response.status_code}")
#         logger.info(f"Response body: {response.text}")

#         if response.status_code in [200, 201]:
#             print(f"✅ SUCCESS: Calendar event created successfully!")
#             return response.json()
#         else:
#             print(f"❌ FAILED: API returned status {response.status_code}")
#             response.raise_for_status()

#     except requests.exceptions.RequestException as e:
#         print(f"❌ REQUEST ERROR: {e}")
#         logger.error(f"Request failed: {e}")
#         raise Exception(f"Calendar API request failed: {e}")
#     except Exception as e:
#         print(f"❌ UNEXPECTED ERROR: {e}")
#         logger.error(f"Unexpected error: {e}")
#         raise





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













def send_contact_form_emails(contact_inquiry, user_ip, page_origin, timestamp):
    """
    Constructs and sends confirmation emails to both the user and the admin.
    
    Args:
        contact_inquiry (Contact): The Contact model instance saved to the database.
        user_ip (str): The IP address of the user.
        page_origin (str): The HTTP_REFERER for the form submission.
        timestamp (str): The formatted timestamp of the submission.
    """
    try:
        # --- HTML Email Template for User ---
        html_content_user = f"""
            <!DOCTYPE html>
            <html lang="en">
            <head>
                <meta charset="UTF-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <title>Thank You - OroShine Dental Care</title>
                <style>
                    /* Styles as provided in the original code */
                    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700&display=swap');
                    
                    * {{ margin: 0; padding: 0; box-sizing: border-box; }}
                    body {{ font-family: 'Inter', 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; line-height: 1.6; color: #333; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 20px; }}
                    .email-container {{ max-width: 600px; margin: 0 auto; background: #ffffff; border-radius: 20px; overflow: hidden; box-shadow: 0 20px 40px rgba(0, 0, 0, 0.1); }}
                    .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 40px 30px; text-align: center; color: white; }}
                    .header h1 {{ font-size: 2.2rem; font-weight: 700; margin-bottom: 10px; }}
                    .header .subtitle {{ font-size: 1.1rem; opacity: 0.9; font-weight: 300; }}
                    .tooth-icon {{ font-size: 3rem; margin-bottom: 20px; }}
                    .content {{ padding: 40px 30px; }}
                    .greeting {{ font-size: 1.3rem; color: #2c3e50; margin-bottom: 25px; font-weight: 600; }}
                    .message-box {{ background: linear-gradient(145deg, #f8f9ff, #e6eaff); border: 2px solid #667eea; border-radius: 15px; padding: 25px; margin: 25px 0; position: relative; }}
                    .message-box::before {{ content: '💬'; position: absolute; top: -10px; left: 20px; background: white; padding: 5px; border-radius: 50%; font-size: 1.2rem; }}
                    .message-box h3 {{ color: #667eea; margin-bottom: 15px; font-size: 1.2rem; }}
                    .user-message {{ background: #fff; padding: 20px; border-radius: 10px; border-left: 4px solid #667eea; font-style: italic; color: #555; line-height: 1.7; }}
                    .steps {{ background: #f8f9fa; border-radius: 15px; padding: 25px; margin: 30px 0; }}
                    .steps h3 {{ color: #2c3e50; margin-bottom: 20px; font-size: 1.3rem; }}
                    .step-item {{ display: flex; align-items: center; margin-bottom: 15px; padding: 15px; background: white; border-radius: 10px; box-shadow: 0 2px 5px rgba(0,0,0,0.1); }}
                    .step-number {{ background: linear-gradient(45deg, #667eea, #764ba2); color: white; width: 30px; height: 30px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-weight: bold; margin-right: 15px; font-size: 0.9rem; }}
                    .emergency-box {{ background: linear-gradient(135deg, #ff6b6b, #ee5a52); color: white; padding: 20px; border-radius: 15px; margin: 25px 0; text-align: center; }}
                    .emergency-box h4 {{ margin-bottom: 10px; font-size: 1.2rem; }}
                    .phone-link {{ color: white; text-decoration: none; font-weight: bold; font-size: 1.3rem; }}
                    .footer {{ background: #2c3e50; color: white; padding: 30px; text-align: center; }}
                    .footer-info {{ margin-bottom: 20px; opacity: 0.8; font-size: 0.9rem; }}
                    .disclaimer {{ background: #34495e; padding: 15px; border-radius: 10px; font-size: 0.85rem; opacity: 0.7; }}
                    @media (max-width: 600px) {{ .email-container {{ margin: 10px; border-radius: 15px; }} .header {{ padding: 30px 20px; }} .content {{ padding: 30px 20px; }} .header h1 {{ font-size: 1.8rem; }} }}
                </style>
            </head>
            <body>
                <div class="email-container">
                    <div class="header">
                        <div class="tooth-icon">🦷</div>
                        <h1>Thank You!</h1>
                        <p class="subtitle">We've received your inquiry</p>
                    </div>
                    <div class="content">
                        <div class="greeting">
                            Dear {contact_inquiry.name},
                        </div>
                        <p>Thank you for reaching out to <strong>OroShine Dental Care</strong>! We're excited to help you achieve your perfect smile.</p>
                        <div class="message-box">
                            <h3>Your Inquiry Subject: {contact_inquiry.subject}</h3>
                            <div class="user-message">
                                {contact_inquiry.message}
                            </div>
                        </div>
                        <div class="steps">
                            <h3>What Happens Next?</h3>
                            <div class="step-item">
                                <div class="step-number">1</div>
                                <div>Our dental team will carefully review your inquiry</div>
                            </div>
                            <div class="step-item">
                                <div class="step-number">2</div>
                                <div>We'll contact you if we need any additional details</div>
                            </div>
                            <div class="step-item">
                                <div class="step-number">3</div>
                                <div>You'll receive our detailed response within 24 hours</div>
                            </div>
                        </div>
                        <div class="emergency-box">
                            <h4>🚨 Need Immediate Assistance?</h4>
                            <p>For dental emergencies, call us right away:</p>
                            <a href="tel:+91XXXXXXXXXX" class="phone-link">+91-XXXXXXXXXX</a>
                        </div>
                    </div>
                    <div class="footer">
                        <div class="footer-info">
                            <p><strong>Submitted on:</strong> {timestamp}</p>
                            <p><strong>Contact Email:</strong> {contact_inquiry.email}</p>
                        </div>
                        <div class="disclaimer">
                            <p>This is an automated confirmation email. Please do not reply to this message.</p>
                            <p>For immediate assistance, please call our clinic directly.</p>
                        </div>
                    </div>
                </div>
            </body>
            </html>
            """

        # Plain text version for user
        text_content_user = f"""
            OROSHINE DENTAL CARE
            
            Dear {contact_inquiry.name},
            
            Thank you for contacting OroShine Dental Care!
            
            We have received your inquiry regarding: {contact_inquiry.subject}
            
            Your message:
            {contact_inquiry.message}
            
            WHAT HAPPENS NEXT?
            1. We will review your inquiry
            2. Contact you if additional details are needed
            3. Provide a response within 24 hours
            
            EMERGENCY CONTACT
            If urgent, call us at +91-XXXXXXXXXX
            
            Submitted on: {timestamp}
            
            This is an automated message. Please do not reply to this email.
            """

        # Send user confirmation email
        email_user = EmailMultiAlternatives(
            subject="✨ Thank You for Contacting OroShine Dental Care",
            body=text_content_user,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[contact_inquiry.email]
        )
        email_user.attach_alternative(html_content_user, "text/html")
        email_user.send(fail_silently=True)

        # --- HTML Email Template for Admin ---
        html_content_admin = f"""
            <!DOCTYPE html>
            <html lang="en">
            <head>
                <meta charset="UTF-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <title>New Contact Inquiry - OroShine Dental Care</title>
                <style>
                    /* Styles as provided in the original code */
                    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700&display=swap');
                    
                    * {{ margin: 0; padding: 0; box-sizing: border-box; }}
                    body {{ font-family: 'Inter', 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; line-height: 1.6; color: #333; background: linear-gradient(135deg, #e74c3c 0%, #c0392b 100%); padding: 20px; }}
                    .email-container {{ max-width: 650px; margin: 0 auto; background: #ffffff; border-radius: 20px; overflow: hidden; box-shadow: 0 20px 40px rgba(0, 0, 0, 0.15); }}
                    .header {{ background: linear-gradient(135deg, #e74c3c 0%, #c0392b 100%); padding: 30px; text-align: center; color: white; position: relative; }}
                    .header::after {{ content: ''; position: absolute; bottom: 0; left: 0; right: 0; height: 3px; background: linear-gradient(90deg, #f39c12, #e67e22, #d35400); }}
                    .alert-icon {{ font-size: 2.5rem; margin-bottom: 15px; animation: pulse 2s infinite; }}
                    @keyframes pulse {{ 0% {{ transform: scale(1); }} 50% {{ transform: scale(1.1); }} 100% {{ transform: scale(1); }} }}
                    .header h1 {{ font-size: 2rem; font-weight: 700; margin-bottom: 8px; }}
                    .header .subtitle {{ font-size: 1rem; opacity: 0.9; font-weight: 300; }}
                    .content {{ padding: 35px 30px; }}
                    .priority-badge {{ display: inline-block; background: linear-gradient(45deg, #f39c12, #e67e22); color: white; padding: 8px 20px; border-radius: 25px; font-weight: 600; font-size: 0.9rem; margin-bottom: 25px; }}
                    .client-info {{ background: linear-gradient(145deg, #f8f9fa, #e9ecef); border-radius: 15px; padding: 25px; margin: 25px 0; border-left: 5px solid #e74c3c; }}
                    .info-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px; margin-bottom: 20px; }}
                    .info-item {{ background: white; padding: 15px; border-radius: 10px; box-shadow: 0 2px 5px rgba(0,0,0,0.1); }}
                    .info-label {{ font-weight: 600; color: #2c3e50; font-size: 0.9rem; margin-bottom: 5px; }}
                    .info-value {{ color: #34495e; font-size: 1rem; word-break: break-all; }}
                    .message-section {{ background: white; border: 2px solid #e74c3c; border-radius: 15px; padding: 25px; margin: 25px 0; position: relative; }}
                    .message-section::before {{ content: '💬'; position: absolute; top: -12px; left: 20px; background: white; padding: 5px 10px; border-radius: 20px; font-size: 1.2rem; }}
                    .message-section h3 {{ color: #e74c3c; margin-bottom: 15px; font-size: 1.3rem; }}
                    .client-message {{ background: #ffeaea; padding: 20px; border-radius: 10px; border-left: 4px solid #e74c3c; font-size: 1.1rem; line-height: 1.7; color: #2c3e50; }}
                    .action-required {{ background: linear-gradient(135deg, #f39c12, #e67e22); color: white; padding: 25px; border-radius: 15px; text-align: center; margin: 25px 0; }}
                    .action-required h3 {{ margin-bottom: 15px; font-size: 1.3rem; }}
                    .response-time {{ background: #27ae60; color: white; padding: 15px 25px; border-radius: 25px; display: inline-block; font-weight: 600; margin-top: 10px; }}
                    .technical-info {{ background: #ecf0f1; padding: 20px; border-radius: 10px; margin-top: 30px; font-size: 0.9rem; }}
                    .technical-info h4 {{ color: #7f8c8d; margin-bottom: 10px; font-size: 1rem; }}
                    .tech-item {{ display: flex; justify-content: space-between; margin-bottom: 8px; padding: 5px 0; }}
                    .tech-label {{ font-weight: 500; color: #34495e; }}
                    .tech-value {{ color: #7f8c8d; font-family: 'Courier New', monospace; }}
                    .footer {{ background: #2c3e50; color: white; padding: 25px; text-align: center; }}
                    .footer-note {{ opacity: 0.8; font-size: 0.9rem; }}
                    @media (max-width: 600px) {{ .email-container {{ margin: 10px; border-radius: 15px; }} .content {{ padding: 25px 20px; }} .info-grid {{ grid-template-columns: 1fr; }} .header h1 {{ font-size: 1.6rem; }} }}
                </style>
            </head>
            <body>
                <div class="email-container">
                    <div class="header">
                        <div class="alert-icon">🚨</div>
                        <h1>New Contact Inquiry</h1>
                        <p class="subtitle">Requires your attention within 24 hours</p>
                    </div>
                    <div class="content">
                        <span class="priority-badge">⚡ High Priority</span>
                        <div class="client-info">
                            <div class="info-grid">
                                <div class="info-item">
                                    <div class="info-label">👤 Client Name</div>
                                    <div class="info-value">{contact_inquiry.name}</div>
                                </div>
                                <div class="info-item">
                                    <div class="info-label">📧 Email Address</div>
                                    <div class="info-value">{contact_inquiry.email}</div>
                                </div>
                                <div class="info-item">
                                    <div class="info-label">📋 Subject</div>
                                    <div class="info-value">{contact_inquiry.subject}</div>
                                </div>
                                <div class="info-item">
                                    <div class="info-label">⏰ Submitted</div>
                                    <div class="info-value">{timestamp}</div>
                                </div>
                            </div>
                        </div>
                        <div class="message-section">
                            <h3>Client Message</h3>
                            <div class="client-message">
                                {contact_inquiry.message}
                            </div>
                        </div>
                        <div class="action-required">
                            <h3>⚡ Action Required</h3>
                            <p>Please respond to this inquiry promptly to maintain our excellent customer service standards.</p>
                            <div class="response-time">Response Required Within 24 Hours</div>
                        </div>
                        <div class="technical-info">
                            <h4>📊 Technical Details</h4>
                            <div class="tech-item">
                                <span class="tech-label">IP Address:</span>
                                <span class="tech-value">{user_ip}</span>
                            </div>
                            <div class="tech-item">
                                <span class="tech-label">Origin Page:</span>
                                <span class="tech-value">{page_origin}</span>
                            </div>
                            <div class="tech-item">
                                <span class="tech-label">Form Source:</span>
                                <span class="tech-value">OroShine Contact Form</span>
                            </div>
                        </div>
                    </div>
                    <div class="footer">
                        <div class="footer-note">
                            <p>This is an automated admin notification from OroShine Dental Care contact system.</p>
                            <p>Please follow up with the client within 24 hours to maintain service quality.</p>
                        </div>
                    </div>
                </div>
            </body>
            </html>
            """
        
        # Plain text version for admin
        text_content_admin = f"""
            ==========================================
            NEW CONTACT FORM SUBMISSION - URGENT
            ==========================================
            
            PRIORITY: HIGH - Response Required Within 24 Hours
            
            CLIENT INFORMATION:
            -------------------
            Name: {contact_inquiry.name}
            Email: {contact_inquiry.email}
            Subject: {contact_inquiry.subject}
            Timestamp: {timestamp}
            
            CLIENT MESSAGE:
            ---------------
            {contact_inquiry.message}
            
            TECHNICAL DETAILS:
            ------------------
            IP Address: {user_ip}
            Origin Page: {page_origin}
            
            ACTION REQUIRED:
            Please follow up with this inquiry within 24 hours.
            
            This is an automated admin notification.
            """

        # Send admin notification email
        '''
        in to add multiple mail ids : missing here 
        '''
        email_admin = EmailMultiAlternatives(
            subject=f"🚨 New Contact Inquiry - {contact_inquiry.name} ({contact_inquiry.subject}) - Response Required",
            body=text_content_admin,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[settings.EMAIL_HOST_USER, "",""], # Add additional admin emails as needed
            reply_to=[contact_inquiry.email]
        )
        email_admin.attach_alternative(html_content_admin, "text/html")
        email_admin.send(fail_silently=True)

    except Exception as mail_error:
        logger.error(f"Email sending failed: {mail_error}", exc_info=True)