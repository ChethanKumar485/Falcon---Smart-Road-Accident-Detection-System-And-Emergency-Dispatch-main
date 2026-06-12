"""
Notification Service - Send alerts to hospitals and police
Supports: SMS (Twilio), Email (SMTP), Webhook
"""
import smtplib
import json
import requests
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
import base64
import os

class NotificationService:
    def __init__(self):
        # Configure these in config.json or environment variables
        self.twilio_sid = os.environ.get('TWILIO_ACCOUNT_SID', '')
        self.twilio_token = os.environ.get('TWILIO_AUTH_TOKEN', '')
        self.twilio_from = os.environ.get('TWILIO_FROM_NUMBER', '')
        self.smtp_host = os.environ.get('SMTP_HOST', 'smtp.gmail.com')
        self.smtp_port = int(os.environ.get('SMTP_PORT', '587'))
        self.smtp_user = os.environ.get('SMTP_USER', '')
        self.smtp_pass = os.environ.get('SMTP_PASS', '')
        self.notification_log = []

    def notify_hospital(self, hospital, accident_data):
        msg = self._build_hospital_message(hospital, accident_data)
        result = {'hospital': hospital['name'], 'status': 'attempted', 'methods': []}
        
        # Try SMS
        if self.twilio_sid:
            sms_result = self._send_sms(hospital.get('phone', ''), msg['sms'])
            result['methods'].append({'type': 'SMS', 'status': sms_result})
        
        # Try Email
        if self.smtp_user:
            email_result = self._send_email(
                f"emergency@{hospital['name'].lower().replace(' ', '')}.in",
                msg['subject'], msg['email']
            )
            result['methods'].append({'type': 'Email', 'status': email_result})
        
        result['status'] = 'sent'
        self.notification_log.append(result)
        print(f"[NOTIFY] Hospital: {hospital['name']} - {msg['sms'][:80]}")
        return result

    def notify_police(self, station, accident_data):
        msg = self._build_police_message(station, accident_data)
        result = {'station': station['name'], 'status': 'attempted', 'methods': []}
        
        if self.twilio_sid:
            sms_result = self._send_sms(station.get('phone', ''), msg['sms'])
            result['methods'].append({'type': 'SMS', 'status': sms_result})
        
        result['status'] = 'sent'
        self.notification_log.append(result)
        print(f"[NOTIFY] Police: {station['name']} - {msg['sms'][:80]}")
        return result

    def _build_hospital_message(self, hospital, data):
        loc = data['location']
        sms = (
            f"🚨 FALCON ACCIDENT ALERT\n"
            f"Accident detected at: {loc['address']}\n"
            f"Time: {data['timestamp_readable']}\n"
            f"Severity: {data.get('severity', 'HIGH')}\n"
            f"Confidence: {int(data['confidence']*100)}%\n"
            f"ETA to hospital: {hospital['eta_minutes']} mins\n"
            f"Please prepare emergency bay immediately.\n"
            f"ID: {data['id']}"
        )
        email = f"""
        <h2 style="color:red">🚨 EMERGENCY ACCIDENT ALERT - FALCON SYSTEM</h2>
        <p><b>Accident ID:</b> {data['id']}</p>
        <p><b>Time:</b> {data['timestamp_readable']}</p>
        <p><b>Location:</b> {loc['address']}</p>
        <p><b>GPS:</b> {loc['lat']}, {loc['lng']}</p>
        <p><b>Severity:</b> <span style="color:red">{data.get('severity','HIGH')}</span></p>
        <p><b>Confidence:</b> {int(data['confidence']*100)}%</p>
        <p><b>ETA:</b> {hospital['eta_minutes']} minutes</p>
        <hr>
        <p>This is an automated alert from the FALCON Smart Road Accident Detection System.</p>
        """
        return {
            'sms': sms,
            'email': email,
            'subject': f"🚨 URGENT: Accident Alert - {loc['address'][:40]}"
        }

    def _build_police_message(self, station, data):
        loc = data['location']
        sms = (
            f"🚔 FALCON ACCIDENT REPORT\n"
            f"Accident at: {loc['address']}\n"
            f"Time: {data['timestamp_readable']}\n"
            f"Severity: {data.get('severity', 'HIGH')}\n"
            f"Coordinates: {loc['lat']:.4f}, {loc['lng']:.4f}\n"
            f"ETA to scene: {station['eta_minutes']} mins\n"
            f"Report ID: {data['id']}\n"
            f"Immediate response required."
        )
        return {'sms': sms, 'subject': f"Accident Alert - {data['id']}"}

    def _send_sms(self, to_number, message):
        try:
            if not self.twilio_sid or not to_number:
                return 'skipped_no_config'
            from twilio.rest import Client
            client = Client(self.twilio_sid, self.twilio_token)
            msg = client.messages.create(body=message, from_=self.twilio_from, to=to_number)
            return f'sent_{msg.sid}'
        except Exception as e:
            return f'failed_{str(e)[:50]}'

    def _send_email(self, to_email, subject, html_body):
        try:
            if not self.smtp_user:
                return 'skipped_no_config'
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = self.smtp_user
            msg['To'] = to_email
            msg.attach(MIMEText(html_body, 'html'))
            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                server.starttls()
                server.login(self.smtp_user, self.smtp_pass)
                server.sendmail(self.smtp_user, to_email, msg.as_string())
            return 'sent'
        except Exception as e:
            return f'failed_{str(e)[:50]}'
