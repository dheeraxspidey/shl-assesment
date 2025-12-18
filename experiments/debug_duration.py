import re

def parse_duration(text):
    print(f"Testing text: '{text}'")
    if not text:
        return 0
    # Current regex
    match = re.search(r'(\d+)\s*min', text, re.IGNORECASE)
    if match:
        return int(match.group(1))
    
    # Proposed regex for "minutes = 11"
    match = re.search(r'minutes\s*=\s*(\d+)', text, re.IGNORECASE)
    if match:
        return int(match.group(1))
        
    return 0

text1 = "Approximate Completion Time in minutes = 11"
text2 = "Duration: 30 mins"

print(f"Result 1: {parse_duration(text1)}")
print(f"Result 2: {parse_duration(text2)}")
