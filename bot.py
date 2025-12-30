import os, requests, time, random, json
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright

# --- Configuration ---
HISTORY_FILE = "posted_urls.txt"
# Source: Curvy Tag (Updated as per your request)
PORN_SOURCE = "https://www.pornpics.com/curvy/"
# Target: Curvy Thread (Updated as per your request)
THREAD_REPLY_URL = "https://exforum.live/threads/curvy-porn-pic-collection.203446/reply"

def get_new_image():
    print(f"--- Step 1: Scraping Thumbnail from {PORN_SOURCE} ---")
    # Headers ko thoda realistic rakha hai taaki block na ho
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Referer': 'https://www.google.com/'
    }
    
    try:
        r = requests.get(PORN_SOURCE, headers=headers, timeout=30)
        if r.status_code != 200:
            print(f"Error: Site responded with status {r.status_code}")
            return None
            
        soup = BeautifulSoup(r.text, 'html.parser')
        
        # History check
        posted = open(HISTORY_FILE, "r").read().splitlines() if os.path.exists(HISTORY_FILE) else []
        
        valid_imgs = []
        # Pornpics ke main page par images 'li' tags ke andar hoti hain
        for img in soup.find_all('img'):
            # Thumbnail kabhi 'data-src' mein hota hai aur kabhi 'src' mein
            src = img.get('data-src') or img.get('src', '')
            
            if not src:
                continue
                
            # Agar URL // se start ho raha ho
            if src.startswith('//'):
                src = 'https:' + src
                
            # Sirf wahi images jo pornpics ke static server par hain aur jo thumbnails hain
            if "pornpics.com" in src and ("/t/" in src or "thumb" in src):
                if src not in posted:
                    valid_imgs.append(src)
        
        # Unique images filter (kaafi baar duplicate links hote hain)
        valid_imgs = list(set(valid_imgs))
        
        if valid_imgs:
            img_url = random.choice(valid_imgs)
            print(f"SUCCESS: Thumbnail Image Found -> {img_url}")
            
            # History update
            with open(HISTORY_FILE, "a") as f: 
                f.write(img_url + "\n")
            return img_url
            
        print("No new thumbnail found on the main page.")
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
    page.set_default_timeout(90000)
    
    try:
        print(f"Opening thread...")
        page.goto(THREAD_REPLY_URL, wait_until="networkidle")
        
        editor = page.locator('.fr-element').first
        editor.wait_for(state="visible")
        print("Editor ready.")

        # --- TOP TEXT ---
        editor.focus()
        page.keyboard.type("[SIZE=6][B]visit website - freepornx.site[/B][/SIZE]\n")
        time.sleep(1)

        # 1. Click Image Toolbar Button
        print("Opening Image Insert Popup...")
        page.click('#insertImage-1', force=True)
        time.sleep(2)

        # 2. Click 'By URL' Tab
        by_url_tab = page.locator('button[data-cmd="imageByURL"], .fr-popup button[data-cmd="imageByURL"]').first
        if by_url_tab.is_visible():
            by_url_tab.click(force=True)
            time.sleep(2)

        # 3. Fill the Direct Image URL
        print("Filling URL box...")
        url_input = page.locator('input[name="src"], .fr-image-by-url-layer input[type="text"], .fr-link-input').first
        url_input.wait_for(state="visible", timeout=20000)
        url_input.fill(direct_url)

        # 4. Insert into editor
        page.keyboard.press("Enter")
        # Image load hone ke liye wait karna padta hai
        time.sleep(10) 

        # --- BOTTOM TEXT ---
        print("Adding footer text...")
        editor.focus()
        page.keyboard.press("Control+End")
        page.keyboard.type("\n[SIZE=10][B]New Fresh Desi Update! 🔥[/B][/SIZE]")
        page.keyboard.type("\n[SIZE=10][B]visit website - freepornx.site[/B][/SIZE]")
        time.sleep(2)

        # 5. Finalize and post
        print("Submitting post...")
        submit_btn = page.locator('button:has-text("Post reply"), .button--icon--reply').first
        submit_btn.click()
        
        page.wait_for_timeout(10000)
        print("--- BOT TASK FINISHED SUCCESSFULLY ---")
        
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
            print("No new image found or scraping failed.")
