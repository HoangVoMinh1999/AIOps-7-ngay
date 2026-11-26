import time
from concurrent.futures import ThreadPoolExecutor
from urllib.request import urlopen

REQUEST_INTERVAL = 0.1


def send_request():
    try:
        with urlopen("http://api:8080/work", timeout=4) as response:
            response.read()
    except OSError as error:
        print(f"Request failed: {error}")


with ThreadPoolExecutor(max_workers=50) as pool:
    next_request = time.monotonic()
    while True:
        pool.submit(send_request)
        next_request = max(next_request + REQUEST_INTERVAL, time.monotonic())
        time.sleep(next_request - time.monotonic())
