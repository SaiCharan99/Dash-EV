"""
Download the WA State EV Population dataset from the official open-data portal.
Run once before starting the app: python download_data.py
Source: Washington State Department of Licensing (data.wa.gov)
"""
import os
import urllib.request

URL = "https://data.wa.gov/api/views/f6w7-q2d2/rows.csv?accessType=DOWNLOAD"
DEST = os.path.join(os.path.dirname(__file__), "data", "ev_population.csv")

os.makedirs(os.path.dirname(DEST), exist_ok=True)

if os.path.exists(DEST):
    size_mb = os.path.getsize(DEST) / 1e6
    print(f"Already downloaded ({size_mb:.0f} MB). Delete {DEST} to re-download.")
else:
    print("Downloading WA EV Population data (~64 MB)...")
    urllib.request.urlretrieve(URL, DEST)
    print(f"Saved to {DEST}")
