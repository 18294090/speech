import requests

def can_connect_to_google():
    url = "https://www.google.com"
    timeout = 5
    try:
        request = requests.get(url, timeout=timeout)
        print("Connected to Google")
    except (requests.ConnectionError, requests.Timeout) as exception:
        print("No internet connection.")
        
can_connect_to_google()