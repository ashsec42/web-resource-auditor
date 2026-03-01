import requests
from bs4 import BeautifulSoup
import time
import csv
import json
import os

CONFIG_FILE = 'config.json'

def load_config():
    if not os.path.exists(CONFIG_FILE):
        print(f"Error: {CONFIG_FILE} not found. Please create it.")
        exit()
    with open(CONFIG_FILE, 'r') as f:
        return json.load(f)

def extract_clean_name(soup):
    """
    Tries to find the most specific test name on the page.
    Prioritizes H1/H2 headers over the generic browser title.
    """
    # Priority 1: Check <h1> tag (Usually the main exam name)
    h1 = soup.find('h1')
    if h1:
        text = h1.get_text(strip=True)
        if len(text) > 3 and "Bodhi" not in text: # Avoid generic site names
            return text

    # Priority 2: Check <h2> tag (Often used for subtitles or specific test names)
    h2 = soup.find('h2')
    if h2:
        text = h2.get_text(strip=True)
        if len(text) > 3:
            return text

    # Priority 3: Check for a specific class (Common in test portals)
    # You can inspect the page to see if they use <div class="test-name">
    specific_class = soup.find(class_="test-name") 
    if specific_class:
        return specific_class.get_text(strip=True)

    # Fallback: Use Browser Title if nothing else is found
    if soup.title:
        return soup.title.string.strip()
    
    return "Unknown Test Name"

def scan():
    config = load_config()
    base_url = config.get("base_url")
    start_id = config.get("start_id")
    scan_range = config.get("range", 10)
    output_file = config.get("output_file", "specific_test_names.csv")
    headers = config.get("headers", {})

    print(f"Scanning for Test Names: {start_id} +/- {scan_range}")

    # Open CSV with 'utf-8-sig' encoding so Excel reads symbols correctly
    with open(output_file, mode='w', newline='', encoding='utf-8-sig') as file:
        writer = csv.writer(file)
        # These are your Excel Headers
        writer.writerow(["ID", "Test Name", "Full URL", "Status"])

        with requests.Session() as session:
            session.headers.update(headers)

            for current_id in range(start_id - scan_range, start_id + scan_range + 1):
                url = f"{base_url}{current_id}"
                
                try:
                    response = session.get(url, timeout=5)
                    
                    if response.status_code == 200:
                        soup = BeautifulSoup(response.text, 'html.parser')

                        # Logic to skip login pages (which always return 200 OK)
                        if "login" in response.url.lower():
                            print(f"[-] ID {current_id}: Redirected to Login")
                            continue

                        # Extract the REAL name
                        test_name = extract_clean_name(soup)

                        print(f"[+] Found: {test_name}")
                        writer.writerow([current_id, test_name, url, "Valid"])

                    else:
                        print(f"[-] Missing: {current_id} (Status {response.status_code})")

                except Exception as e:
                    print(f"[!] Error on {current_id}: {e}")

                time.sleep(config.get("delay", 0.5))

    print(f"\nDone. Open '{output_file}' in Excel.")

if __name__ == "__main__":
    scan()
