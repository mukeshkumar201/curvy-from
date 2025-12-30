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
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
    }
    
    try:
        r = requests.get(PORN_SOURCE, headers=headers, timeout=30)
        print(f"DEBUG: Site Status Code: {r.status_code}")
        
        if r.status_code != 200:
            print("ERROR: Website ne access block kiya hai (Status Code 403/503).")
            return None
            
        soup = BeautifulSoup(r.text, 'html.parser')
        posted = open(HISTORY_FILE, "r").read().splitlines() if os.path.exists(HISTORY_FILE) else []
        
        valid_imgs = []
        # Saare images dhundo
        all_imgs = soup.find_all('img')
        print(f"DEBUG: Total images found on page: {len(all_imgs)}")

        for img in all_imgs:
            # Check for multiple possible source attributes (Lazy loading fix)
            src = img.get('data-src') or img.get('src') or img.get('data-original') or img.get('data-lazy-src')
            
            if not src:
                continue
                
            # Normalize URL
            if src.startswith('//'):
                src = 'https:' + src
            elif src.startswith('/'):
                src = 'https://www.pornpics.com' + src
            
            # Sirf PornPics ki real images uthao (Ads ya small icons filter karo)
            if "pornpics.com" in src:
                # 't' stands for thumbnail in PornPics
                if "/t/" in src or "thumb" in src or "images." in src:
                    if src not in posted:
                        valid_imgs.append(src)

        # Unique images filter
        valid_imgs = list(set(valid_imgs))
        print(f"DEBUG: Valid unique thumbnails found: {len(valid_imgs)}")
        
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
    browser = p.chromium.launch(headless=True, args=["--no-sandbox", "--disable-setuid-sandbox"])
    context = browser.new_context(user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")
    
    cookies_raw = os.environ.get('EX_COOKIES')
    if not cookies_raw:
        print("CRITICAL: EX_COOKIES missing!")
        return
        
    context.add_cookies(json.loads(cookies_raw))
    page = context.new_page()
    
    try:
        print(f"Opening thread...")
        page.goto(THREAD_REPLY_URL, wait_until="domcontentloaded", timeout=60000)
        
        # Editor wait logic
        editor = page.locator('.fr-element').first
        editor.wait_for(state="visible", timeout=30000)
        
        # --- TOP TEXT ---
        editor.focus()
        page.keyboard.type("[SIZE=6][B]visit website - freepornx.site[/B][/SIZE]\n")
        time.sleep(2)

        # Image Insert
        print("Inserting image via URL...")
        page.click('#insertImage-1', force=True)
        time.sleep(1)
        
        # Click 'By URL' tab if available
        by_url = page.locator('button[data-cmd="imageByURL"]').first
        if by_url.is_visible():
            by_url.click()
            time.sleep(1)

        url_input = page.locator('input[name="src"]').first
        url_input.fill(direct_url)
        page.keyboard.press("Enter")
        
        # Wait for image to load in editor
        time.sleep(10) 

        # --- BOTTOM TEXT ---
        page.keyboard.press("Control+End")
        page.keyboard.type("\n[SIZE=10][B]New Fresh Desi Update! 🔥[/B][/SIZE]")
        page.keyboard.type("\n[SIZE=10][B]visit website - freepornx.site[/B][/SIZE]")
        time.sleep(2)

        # Post Reply
        submit_btn = page.locator('button:has-text("Post reply")').first
        submit_btn.click()
        
        print("--- POST SUBMITTED ---")
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
            print("No new image found. Check Debug logs above.")
