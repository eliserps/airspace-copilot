import requests
from config import OPENSKY_CLIENT_ID, OPENSKY_CLIENT_SECRET

TOKEN_URL = "https://auth.opensky-network.org/auth/realms/opensky-network/protocol/openid-connect/token"
API_URL = "https://opensky-network.org/api/states/all"

def get_token():
   """Exchanges client credentials for a short-lived access token (~30 min)."""
   response = requests.post(
       TOKEN_URL,
       data={
           "grant_type": "client_credentials",
           "client_id": OPENSKY_CLIENT_ID,
           "client_secret": OPENSKY_CLIENT_SECRET,
       },
   )
   response.raise_for_status()
   return response.json()["access_token"]

def get_aircraft(token, lamin, lamax, lomin, lomax):
   """Fetches live aircraft inside a bounding box (south, north, west, east)."""
   response = requests.get(
       API_URL,
       headers={"Authorization": f"Bearer {token}"},
       params={"lamin": lamin, "lamax": lamax, "lomin": lomin, "lomax": lomax},
   )
   response.raise_for_status()
   return response.json()["states"] or []