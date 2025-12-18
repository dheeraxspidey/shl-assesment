import requests
from bs4 import BeautifulSoup

url = "https://www.shl.com/products/product-catalog/view/account-manager-solution/"
headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"}

try:
    response = requests.get(url, headers=headers)
    soup = BeautifulSoup(response.text, "html.parser")
    
    print("\n--- Current Test Type Logic (Simulation) ---")
    full_text = soup.get_text(" ", strip=True)
    test_type = []
    if "Knowledge" in full_text: test_type.append("Knowledge & Skills")
    if "Ability" in full_text: test_type.append("Ability & Aptitude")
    if "Personality" in full_text: test_type.append("Personality")
    print(f"Current Logic Result: {test_type}")

    print("\n--- Proposed Logic ---")
    # Find the row containing "Test Type"
    rows = soup.find_all("div", class_="product-catalogue-training-calendar__row")
    found_types = []
    
    # Mapping based on the tooltip in the HTML provided by user
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

    for row in rows:
        if "Test Type:" in row.get_text():
            keys = row.find_all("span", class_="product-catalogue__key")
            for k in keys:
                code = k.get_text(strip=True)
                if code in type_map:
                    found_types.append(type_map[code])
                else:
                    found_types.append(code) # Fallback
            break
            
    print(f"Proposed Logic Result: {found_types}")

except Exception as e:
    print(f"Error: {e}")
