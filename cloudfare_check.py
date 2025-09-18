import requests
import time
from config import CLOUDFLARE_VERIFY_URL, USER_AGENT

def verify_cloudflare_protection():
    """
    Verify Cloudflare protection is active by making a test request
    Returns True if Cloudflare protection is detected
    """
    try:
        headers = {
            'User-Agent': USER_AGENT
        }
        
        response = requests.get(CLOUDFLARE_VERIFY_URL, headers=headers, timeout=10)
        
        # Check for Cloudflare-specific headers
        cloudflare_headers = [
            'cf-ray',
            'cf-cache-status',
            'cf-request-id'
        ]
        
        has_cloudflare = any(header in response.headers for header in cloudflare_headers)
        
        # Also check for Cloudflare challenge page
        if has_cloudflare or 'cloudflare' in response.text.lower():
            return True
            
        return False
        
    except requests.exceptions.RequestException as e:
        print(f"Cloudflare verification failed: {e}")
        return False

def bypass_cloudflare_challenge(url, max_retries=3):
    """
    Attempt to bypass Cloudflare challenge if encountered
    """
    for attempt in range(max_retries):
        try:
            session = requests.Session()
            headers = {
                'User-Agent': USER_AGENT,
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
            }
            
            response = session.get(url, headers=headers, timeout=30)
            
            # If we get a challenge page, wait and retry
            if response.status_code == 403 and 'challenge' in response.text.lower():
                time.sleep(5)  # Wait before retry
                continue
                
            return response
            
        except requests.exceptions.RequestException as e:
            print(f"Attempt {attempt + 1} failed: {e}")
            time.sleep(3)
    
    return None

if __name__ == "__main__":
    # Test Cloudflare protection
    is_protected = verify_cloudflare_protection()
    print(f"Cloudflare protection active: {is_protected}")