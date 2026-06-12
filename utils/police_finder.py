"""
Police Station Finder - Uses OpenStreetMap Overpass API
"""
import requests
import random
import math

OFFICER_NAMES = [
    'SI Ramesh Nayak', 'ASI Pradeep Kumar', 'HC Suresh Babu',
    'SI Meera Pillai', 'ASI Vikram Singh', 'HC Anand Reddy',
    'SI Fatima Begum', 'ASI Rajan Krishnan', 'HC Deepak Yadav'
]

class PoliceFinder:
    def find_nearby(self, lat, lng, address, radius=5000):
        stations = self._fetch_from_osm(lat, lng, radius)
        if not stations:
            stations = self._get_demo_stations(lat, lng, address)
        return stations[:4]

    def _fetch_from_osm(self, lat, lng, radius):
        try:
            query = f"""
            [out:json][timeout:10];
            (
              node["amenity"="police"](around:{radius},{lat},{lng});
              way["amenity"="police"](around:{radius},{lat},{lng});
            );
            out center 6;
            """
            resp = requests.post(
                'https://overpass-api.de/api/interpreter',
                data={'data': query},
                timeout=12
            )
            if resp.status_code != 200:
                return []
            data = resp.json()
            stations = []
            for el in data.get('elements', [])[:4]:
                tags = el.get('tags', {})
                s_lat = el.get('lat') or el.get('center', {}).get('lat', lat)
                s_lng = el.get('lon') or el.get('center', {}).get('lon', lng)
                dist = self._haversine(lat, lng, s_lat, s_lng)
                name = tags.get('name', 'Police Station')
                officers = self._gen_officers()
                stations.append({
                    'name': name,
                    'lat': s_lat,
                    'lng': s_lng,
                    'distance_km': round(dist, 2),
                    'address': tags.get('addr:full') or tags.get('addr:street', f'Police Station, Sector'),
                    'phone': tags.get('phone') or self._gen_phone(),
                    'jurisdiction': tags.get('jurisdiction', 'Local'),
                    'officers': officers,
                    'available_officers': sum(1 for o in officers if o['on_duty']),
                    'eta_minutes': max(5, int(dist * 3)),
                    'station_id': f"PS{random.randint(100,999)}"
                })
            stations.sort(key=lambda x: x['distance_km'])
            return stations
        except Exception as e:
            print(f"OSM police fetch error: {e}")
            return []

    def _get_demo_stations(self, lat, lng, address):
        offsets = [(0.015, 0.02), (-0.02, 0.01), (0.025, -0.015), (-0.01, -0.025)]
        names = [
            'MG Road Police Station', 'Koramangala Police Station',
            'Indiranagar Police Station', 'Whitefield Police Station'
        ]
        stations = []
        for i, (dlat, dlng) in enumerate(offsets):
            s_lat, s_lng = lat + dlat, lng + dlng
            dist = self._haversine(lat, lng, s_lat, s_lng)
            officers = self._gen_officers()
            stations.append({
                'name': names[i],
                'lat': s_lat,
                'lng': s_lng,
                'distance_km': round(dist, 2),
                'address': f'Main Road, Sector {i+1}, {address}',
                'phone': self._gen_phone(),
                'jurisdiction': 'Karnataka Police',
                'officers': officers,
                'available_officers': sum(1 for o in officers if o['on_duty']),
                'eta_minutes': max(5, int(dist * 3)),
                'station_id': f"PS{random.randint(100,999)}"
            })
        stations.sort(key=lambda x: x['distance_km'])
        return stations

    def _gen_officers(self):
        count = random.randint(2, 5)
        officers = []
        for name in random.sample(OFFICER_NAMES, min(count, len(OFFICER_NAMES))):
            officers.append({
                'name': name,
                'rank': name.split(' ')[0],
                'badge': f"KA{random.randint(1000,9999)}",
                'on_duty': random.random() > 0.4
            })
        return officers

    def _gen_phone(self):
        return f"100 / +91-{random.randint(80000,99999)}{random.randint(10000,99999)}"

    def _haversine(self, lat1, lon1, lat2, lon2):
        R = 6371
        dlat = math.radians(lat2 - lat1)
        dlon = math.radians(lon2 - lon1)
        a = math.sin(dlat/2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon/2)**2
        return R * 2 * math.asin(math.sqrt(a))
