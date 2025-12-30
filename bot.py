import os, requests, time, random, json
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright

# --- Configuration ---
HISTORY_FILE = "posted_urls.txt"
PORN_SOURCE = "https://www.pornpics.com/curvy/"
THREAD_REPLY_URL = "https://exforum.live/threads/curvy-porn-pic-collection.203446/reply"

def get_new_image():
    print(f"--- Step 1: Scraping Thumbnail from {PORN_SOURCE} ---")
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    }
    
    try:
        r = requests.get(PORN_SOURCE, headers=headers, timeout=30)
        print(f"DEBUG: Site Status Code: {r.status_code}")
        
        soup = BeautifulSoup(r.text, 'html.parser')
        posted = open(HISTORY_FILE, "r").read().splitlines() if os.path.exists(HISTORY_FILE) else []
        
        valid_imgs = []
        all_imgs = soup.find_all('img')
        print(f"DEBUG: Total images found on page: {len(all_imgs)}")

        for img in all_imgs:
            # Har possible attribute check karo jahan image link ho sakta hai
            src = img.get('data-src') or img.get('src') or img.get('data-original') or img.get('data-lazy')
            
            if not src:
                continue
            
            # URL ko complete (absolute) karo
            if src.startswith('//'):
                src = 'https:' + src
            elif src.startswith('/') and not src.startswith('//'):
                src = 'https://www.pornpics.com' + src
            
            # Filter: Hum ads aur icons ko nikal rahe hain
            # Thumbnail aksar 'pornpics.com' ke static servers par hoti hain
            # Maine filter thoda wide kiya hai (sirf 'logo' aur 'icon' ko exclude kiya hai)
            if "pornpics.com" in src and "logo" not in src.lower() and "icon" not in src.lower():
                if src not in posted:
                    valid_imgs.append(src)
                else:
                    # Agar aapko lag raha hai ki sab 'posted' dikha raha hai toh ye line debug karegi
                    pass 

        # Sirf pehle 3 images print karo debug ke liye
        if all_imgs:
            print(f"DEBUG Sample URLs found: {[img.get('src') for img in all_imgs[:3]]}")

        valid_imgs = list(set(valid_imgs))
        print(f"DEBUG: Valid unique thumbnails after filtering: {len(valid_imgs)}")
        
        if valid_imgs:
            img_url = random.choice(valid_imgs)
            print(f"SUCCESS: Thumbnail Found -> {img_url}")
            with open(HISTORY_FILE, "a") as f: 
                f.write(img_url + "\n")
            return img_url
            
        return None
        
    except Exception as e:
        print(f"Scrape Error: {e}")
        return None

def post_to_forum(p, direct_url):
    print("--- Step 2: Posting Direct URL to Forum ---")
    browser = p.chromium.launch(headless=True, args=["--no-sandbox"])
    context = browser.new_context(user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")
    
    cookies_raw = os.environ.get('EX_COOKIES')
    if not cookies_raw:
        print("CRITICAL: EX_COOKIES missing!")
        return
        
    context.add_cookies(json.loads(cookies_raw))
    page = context.new_page()
    
    try:
        print(f"Opening thread...")
        page.goto(THREAD_REPLY_URL, wait_until="networkidle", timeout=60000)
        
        editor = page.locator('.fr-element').first
        editor.wait_for(state="visible", timeout=30000)
        
        # --- TOP TEXT ---
        editor.focus()
        page.keyboard.type("[SIZE=6][B]visit website - freepornx.site[/B][/SIZE]\n")
        time.sleep(2)

        # Image Insert
        print("Inserting image via URL...")
        page.click('#insertImage-1', force=True)
        time.sleep(2)
        
        # URL input ko target karna
        url_input = page.locator('input[name="src"], .fr-link-input').first
        url_input.fill(direct_url)
        page.keyboard.press("Enter")
        
        time.sleep(10) # Wait for image load

        # --- BOTTOM TEXT ---
        page.keyboard.press("Control+End")
        page.keyboard.type("\n[SIZE=10][B]New Fresh Desi Update! 🔥[/B][/SIZE]")
        page.keyboard.type("\n[SIZE=10][B]visit website - freepornx.site[/B][/SIZE]")
        time.sleep(2)

        # Post Reply
        submit_btn = page.locator('button:has-text("Post reply")').first
        submit_btn.click()
        
        print("--- BOT TASK FINISHED SUCCESSFULLY ---")
        time.sleep(5)
        
    except Exception as e:
        print(f"Forum Error: {e}")
    finally:
        browser.close()

if __name__ == "__main__":
    with sync_playwright() as playwright:
        img_url = get_new_image()
        if img_url:
            post_to_forum(playwright, img_url)
        else:
            print("No new image found. Filtering logic check required.")
