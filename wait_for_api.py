import sys
import time
import requests

if len(sys.argv) < 2:
    print("Usage: python wait_for_api.py <url> [timeout]")
    sys.exit(1)

url = sys.argv[1]
timeout = int(sys.argv[2]) if len(sys.argv) > 2 else 60

start = time.time()
while True:
    try:
        r = requests.get(url)
        if r.status_code == 200:
            print(f"API is up at {url}!")
            break
    except Exception:
        pass
    if time.time() - start > timeout:
        print(f"Timeout waiting for API at {url}")
        sys.exit(1)
    print(f"API not up yet at {url}, waiting...")
    time.sleep(1)
