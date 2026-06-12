"""
Location Service - Get current location via IP or GPS
"""
import requests
import json

class LocationService:
    def __init__(self):
        self.cached_location = None

    def get_location(self):
        try:
            # Try IP-based location
            resp = requests.get('https://ipapi.co/json/', timeout=5)
            if resp.status_code == 200:
                data = resp.json()
                loc = {
                    'lat': data.get('latitude', 12.9716),
                    'lng': data.get('longitude', 77.5946),
                    'address': f"{data.get('city', 'Unknown')}, {data.get('region', '')}, {data.get('country_name', '')}",
                    'city': data.get('city', 'Unknown'),
                    'region': data.get('region', ''),
                    'country': data.get('country_name', ''),
                    'postal': data.get('postal', '')
                }
                self.cached_location = loc
                return loc
        except:
            pass

        # Fallback to Bengaluru
        return {
            'lat': 12.9716,
            'lng': 77.5946,
            'address': 'Bengaluru, Karnataka, India',
            'city': 'Bengaluru',
            'region': 'Karnataka',
            'country': 'India',
            'postal': '560001'
        }

    def reverse_geocode(self, lat, lng):
        try:
            url = f"https://nominatim.openstreetmap.org/reverse?lat={lat}&lon={lng}&format=json"
            resp = requests.get(url, headers={'User-Agent': 'FalconADS/1.0'}, timeout=5)
            if resp.status_code == 200:
                data = resp.json()
                addr = data.get('address', {})
                return {
                    'lat': lat,
                    'lng': lng,
                    'address': data.get('display_name', f'{lat}, {lng}'),
                    'city': addr.get('city') or addr.get('town') or addr.get('village', 'Unknown'),
                    'region': addr.get('state', ''),
                    'country': addr.get('country', ''),
                    'postal': addr.get('postcode', '')
                }
        except:
            pass
        return {'lat': lat, 'lng': lng, 'address': f'{lat:.4f}, {lng:.4f}', 'city': 'Unknown', 'region': '', 'country': ''}
