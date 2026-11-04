import urllib.request
import time

# Wait for Streamlit to start
time.sleep(3)

try:
    req = urllib.request.Request("http://localhost:8501/")
    with urllib.request.urlopen(req, timeout=10) as response:
        print(f"HTTP Status: {response.status}")
        html = response.read().decode("utf-8", errors="replace")
        print(f"HTML Length: {len(html)}")
        if "streamlit" in html.lower():
            print("Streamlit app is running!")
        else:
            print("Warning: Streamlit content not detected")
except Exception as e:
    print(f"Could not connect to Streamlit app: {e}")
    print("The app may still be starting or there may be an error.")
