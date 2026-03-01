import requests
from bs4 import BeautifulSoup
import time
import csv
import json
import os

# Configuration file name
CONFIG_FILE = 'config.json'

def load_config():
    """Load settings from the external config file."""
    if not os.path.exists(CONFIG_FILE):
        print(f"Error: {CONFIG_FILE} not found. Please create it.")
        exit()
    with open(CONFIG_FILE, 'r') as f:
        return json.load(f)

def scan():
    config = load_config()
    
    # Load parameters from config
    base_url = config.get("base_url")
    start_id = config.get("start_id")
    scan_range = config.get("range", 10)
    output_file = config.get("output_file", "results.csv")
    headers = config.get("headers", {})
    
    # Calculate range
    id_min = start_id - scan_range
    id_max = start_id + scan_range

    print(f"Starting scan: {id_min} to {id_max}")
    print(f"Target Base: {base_url}")

    with open(output_file, mode='w', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        writer.writerow(["ID", "Extracted Name", "URL", "Status"])

        with requests.Session() as session:
            # Apply headers (User-Agent, Cookies, etc.)
            session.headers.update(headers)

            for current_id in range(id_min, id_max + 1):
                url = f"{base_url}{current_id}"
                
                try:
                    response = session.get(url, timeout=5)
                    
                    if response.status_code == 200:
                        soup = BeautifulSoup(response.text, 'html.parser')
                        
                        # Generic logic: Try to find the page title
                        page_title = "Unknown"
                        if soup.title:
                            page_title = soup.title.string.strip()
                        
                        # If a specific CSS selector is provided in config, try that instead
                        # This allows targeting specific <h1> or <div> tags without changing code
                        if config.get("title_selector"):
                            element = soup.select_one(config.get("title_selector"))
                            if element:
                                page_title = element.get_text(strip=True)

                        # Filter: Skip if URL redirected to a login page (common issue)
                        if "login" not in response.url.lower():
                            print(f"[+] Found ({current_id}): {page_title}")
                            writer.writerow([current_id, page_title, url, response.status_code])
                        else:
                            print(f"[-] Redirected ({current_id})")
                    else:
                        print(f"[-] Missing ({current_id}): Status {response.status_code}")

                except Exception as e:
                    print(f"[!] Error on {current_id}: {str(e)}")

                # Delay to be polite
                time.sleep(config.get("delay", 1))

    print(f"\nDone. Results saved to {output_file}")

if __name__ == "__main__":
    scan()
