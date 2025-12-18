import requests
from bs4 import BeautifulSoup
import json
import time
import re
import os

BASE_URL = "https://www.shl.com/solutions/products/product-catalog/"
OUTPUT_FILE = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "raw_assessments.json")

def get_soup(url):
    retries = 3
    for i in range(retries):
        try:
            response = requests.get(url, headers={"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"})
            if response.status_code == 200:
                return BeautifulSoup(response.text, "html.parser")
            print(f"Failed to fetch {url}: Status {response.status_code}")
        except Exception as e:
            print(f"Error fetching {url}: {e}")
        time.sleep(2)
    return None

def parse_duration(text):
    if not text:
        return 0
    match = re.search(r'(\d+)\s*min', text, re.IGNORECASE)
    if match:
        return int(match.group(1))
        
    # Handle "minutes = 11" format
    match = re.search(r'minutes\s*=\s*(\d+)', text, re.IGNORECASE)
    if match:
        return int(match.group(1))
        
    return 0

def scrape_product_details(url):
    # print(f"  Scraping details from {url}...")
    soup = get_soup(url)
    if not soup:
        return None
        
    try:
        # Title
        title_elem = soup.find("h1")
        name = title_elem.get_text(strip=True) if title_elem else "Unknown"
        
        # Description
        description = ""
        rows = soup.find_all("div", class_="product-catalogue-training-calendar__row")
        for row in rows:
            h4 = row.find("h4")
            if h4 and "Description" in h4.get_text(strip=True):
                # Get all text from paragraphs in this row
                ps = row.find_all("p")
                description = " ".join([p.get_text(strip=True) for p in ps])
                break
        
        # Fallback if specific structure not found (though unlikely for valid pages)
        if not description:
             desc_elem = soup.find("div", class_="rich-text")
             if desc_elem:
                 description = desc_elem.get_text(strip=True)
            
        # Metadata
        full_text = soup.get_text(" ", strip=True)
        
        # Initialize fields
        duration = 0
        job_levels = []
        languages = []
        
        # Extract metadata from rows
        rows = soup.find_all("div", class_="product-catalogue-training-calendar__row")
        for row in rows:
            h4 = row.find("h4")
            if not h4: continue
            
            header_text = h4.get_text(strip=True)
            
            if "Assessment length" in header_text:
                p_text = row.find("p").get_text(strip=True)
                duration = parse_duration(p_text)
                
            elif "Job levels" in header_text:
                p_text = row.find("p").get_text(strip=True)
                # Split by comma and clean
                job_levels = [level.strip() for level in p_text.split(',') if level.strip()]
                
            elif "Languages" in header_text:
                p_text = row.find("p").get_text(strip=True)
                languages = [lang.strip() for lang in p_text.split(',') if lang.strip()]

        # Fallback for duration if not found in specific row
        if duration == 0:
            duration = parse_duration(full_text)
        
        test_type = []
        # Map codes to full names
        type_map = {
            "A": "Ability & Aptitude",
            "B": "Biodata & Situational Judgement",
            "C": "Competencies",
            "D": "Development & 360",
            "E": "Assessment Exercises",
            "K": "Knowledge & Skills",
            "P": "Personality & Behavior",
            "S": "Simulations"
        }
        
        # Find the row containing "Test Type"
        rows = soup.find_all("div", class_="product-catalogue-training-calendar__row")
        for row in rows:
            if "Test Type" in row.get_text():
                keys = row.find_all("span", class_="product-catalogue__key")
                for k in keys:
                    code = k.get_text(strip=True)
                    if code in type_map:
                        test_type.append(type_map[code])
                    else:
                        test_type.append(code)
                break
        
        if not test_type: 
            # Fallback if specific section not found, but be careful not to include everything
            if "Knowledge" in full_text: test_type.append("Knowledge & Skills")
            if "Ability" in full_text: test_type.append("Ability & Aptitude")
            if "Personality" in full_text: test_type.append("Personality")
            if not test_type: test_type.append("General")
        
        remote_support = "Yes" if "remote" in full_text.lower() else "No"
        adaptive_support = "Yes" if "adaptive" in full_text.lower() else "No"
        
        if "Pre-packaged Job Solutions" in full_text:
            return None
            
        return {
            "name": name,
            "url": url,
            "description": description,
            "duration": duration,
            "job_levels": job_levels,
            "languages": languages,
            "test_type": test_type,
            "remote_support": remote_support,
            "adaptive_support": adaptive_support
        }
        
    except Exception as e:
        print(f"  Error parsing details: {e}")
        return None

def scrape_catalog():
    assessments = []
    seen_urls = set()
    start = 0
    BATCH_SIZE = 12 # Updated batch size
    
    # Load existing data
    if os.path.exists(OUTPUT_FILE):
        try:
            with open(OUTPUT_FILE, 'r') as f:
                assessments = json.load(f)
                print(f"Loaded {len(assessments)} existing assessments.")
                for item in assessments:
                    seen_urls.add(item['url'])
                
                # Resume from the next batch aligned offset
                # This ensures we cover any potentially missed items in the last partial batch
                # start = (len(assessments) // BATCH_SIZE) * BATCH_SIZE
                pass
        except Exception as e:
            print(f"Error loading existing data: {e}")
            assessments = []
            start = 0
            
    print(f"Resuming scraping from start={start}...")
    
    while True:
        print(f"Scraping start={start}...")
        url = f"{BASE_URL}?start={start}&type=1" # Updated URL structure
        soup = get_soup(url)
        
        if not soup:
            break
            
        links = soup.find_all("a", href=True)
        product_links = []
        for l in links:
            href = l['href']
            if '/products/product-catalog/view/' in href:
                full_url = href if href.startswith("http") else "https://www.shl.com" + href
                if full_url not in seen_urls:
                    product_links.append(full_url)
                    seen_urls.add(full_url)
        
        if not product_links:
            # If we found no NEW links, but we might be on a page we already fully scraped.
            # We should check if there are ANY product links on the page to decide if we reached the end.
            # But the logic above filters by seen_urls.
            # If we re-scrape the last batch, we might find 0 new links.
            # So we shouldn't break immediately if it's the first resumed batch.
            # Let's check if the page actually has products.
            all_product_links = [l['href'] for l in links if '/products/product-catalog/view/' in l['href']]
            if not all_product_links:
                print("No products found on this page. Stopping.")
                break
            elif not product_links:
                 print(f"No new products found at start={start} (all seen). Moving to next batch.")
        
        if product_links:
            print(f"Found {len(product_links)} new products at start={start}.")
            
            for link in product_links:
                details = scrape_product_details(link)
                if details:
                    assessments.append(details)
                    # Save incrementally after each item to be safe
                    with open(OUTPUT_FILE, 'w') as f:
                        json.dump(assessments, f, indent=2)
                
        start += BATCH_SIZE
            
    print(f"Final count: {len(assessments)} assessments saved to {OUTPUT_FILE}")

if __name__ == "__main__":
    scrape_catalog()
