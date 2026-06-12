"""
WhatsApp Service - Send accident alerts via WhatsApp
Uses Twilio WhatsApp API (sandbox or production)
Also supports Meta WhatsApp Business API
"""
import os
import json
import requests
import base64
from datetime import datetime

class WhatsAppService:
    def __init__(self):
        self.twilio_sid = os.environ.get('TWILIO_ACCOUNT_SID', '')
        self.twilio_token = os.environ.get('TWILIO_AUTH_TOKEN', '')
        self.twilio_whatsapp_from = os.environ.get('TWILIO_WHATSAPP_FROM', 'whatsapp:+14155238886')
        self.meta_token = os.environ.get('META_WHATSAPP_TOKEN', '')
        self.meta_phone_id = os.environ.get('META_PHONE_NUMBER_ID', '')
        # Comma-separated list of WhatsApp numbers to notify
        self.alert_numbers = os.environ.get('WHATSAPP_ALERT_NUMBERS', '').split(',')
        self.log = []

    def send_accident_alert(self, accident_data):
        results = []
        message = self._build_message(accident_data)

        for number in self.alert_numbers:
            number = number.strip()
            if not number:
                continue
            if self.twilio_sid:
                r = self._send_via_twilio(number, message, accident_data)
            elif self.meta_token:
                r = self._send_via_meta(number, message, accident_data)
            else:
                r = {'number': number, 'status': 'not_configured', 'note': 'Add Twilio or Meta credentials'}
            results.append(r)
            self.log.append(r)

        if not results:
            return {
                'success': False,
                'message': 'No WhatsApp numbers configured. Add WHATSAPP_ALERT_NUMBERS to environment.',
                'results': []
            }

        return {'success': True, 'results': results, 'count': len(results)}

    def _build_message(self, data):
        loc = data['location']
        map_link = f"https://www.google.com/maps?q={loc['lat']},{loc['lng']}"
        msg = (
            f"🚨 *FALCON ACCIDENT ALERT* 🚨\n\n"
            f"📍 *Location:* {loc['address']}\n"
            f"🕐 *Time:* {data['timestamp_readable']}\n"
            f"⚠️ *Severity:* {data.get('severity', 'HIGH')}\n"
            f"🎯 *Confidence:* {int(data['confidence']*100)}%\n"
            f"🆔 *Incident ID:* {data['id']}\n\n"
            f"🏥 *Nearest Hospital:* {data['hospitals'][0]['name'] if data.get('hospitals') else 'Locating...'}\n"
            f"🚔 *Nearest Police:* {data['police_stations'][0]['name'] if data.get('police_stations') else 'Locating...'}\n\n"
            f"📌 *Map:* {map_link}\n\n"
            f"_Automated alert from FALCON Smart Detection System_"
        )
        return msg

    def _send_via_twilio(self, number, message, accident_data):
        try:
            from twilio.rest import Client
            client = Client(self.twilio_sid, self.twilio_token)
            to_wa = f"whatsapp:{number}" if not number.startswith('whatsapp:') else number
            msg = client.messages.create(
                body=message,
                from_=self.twilio_whatsapp_from,
                to=to_wa
            )
            return {'number': number, 'status': 'sent', 'sid': msg.sid}
        except Exception as e:
            return {'number': number, 'status': 'failed', 'error': str(e)[:100]}

    def _send_via_meta(self, number, message, accident_data):
        try:
            url = f"https://graph.facebook.com/v18.0/{self.meta_phone_id}/messages"
            headers = {
                'Authorization': f'Bearer {self.meta_token}',
                'Content-Type': 'application/json'
            }
            payload = {
                'messaging_product': 'whatsapp',
                'to': number.replace('+', '').replace(' ', ''),
                'type': 'text',
                'text': {'body': message}
            }
            resp = requests.post(url, headers=headers, json=payload, timeout=10)
            if resp.status_code == 200:
                return {'number': number, 'status': 'sent', 'response': resp.json()}
            return {'number': number, 'status': 'failed', 'error': resp.text[:100]}
        except Exception as e:
            return {'number': number, 'status': 'failed', 'error': str(e)[:100]}

    def send_to_number(self, number, message):
        """Send custom WhatsApp message to specific number"""
        if self.twilio_sid:
            return self._send_via_twilio(number, message, {})
        elif self.meta_token:
            return self._send_via_meta(number, message, {})
        return {'status': 'not_configured'}
