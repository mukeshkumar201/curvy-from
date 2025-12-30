import os, requests, time, random, json
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright

# --- Configuration ---
HISTORY_FILE = "posted_urls.txt"
# Source: Indian Pussy Tag
PORN_SOURCE = "https://www.pornpics.com/tags/indian-pussy/"
# Target: Desi Pussy Collection Thread
THREAD_REPLY_URL = "https://exforum.live/threads/desi-pussy-collection.203442/reply"

def get_new_image():
    print(f"--- Step 1: Scraping Thumbnail from {PORN_SOURCE} ---")
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
    try:
        r = requests.get(PORN_SOURCE, headers=headers, timeout=30)
        soup = BeautifulSoup(r.text, 'html.parser')
        
        # Yahan hum gallery ke andar nahi ja rahe, seedha main page ki images (thumbnails) utha rahe hain
        posted = open(HISTORY_FILE, "r").read().splitlines() if os.path.exists(HISTORY_FILE) else []
        
        # Main page par images aksar 'data-src' ya 'src' mein hoti hain
        # Hum sirf wahi images le rahe hain jinme 'pornpics.com' ho (ads ya logos ko filter karne ke liye)
        valid_imgs = []
        for img in soup.find_all('img'):
            src = img.get('data-src') or img.get('src', '')
            # Thumbnail images aksar 't.pornpics.com' ya 'thumb' patterns mein hoti hain
            if "pornpics.com" in src and "http" in src:
                valid_imgs.append(src)
        
        # History check: Wo image jo pehle post nahi hui
        new_imgs = [u for u in valid_imgs if u not in posted]
        
        if new_imgs:
            img_url = random.choice(new_imgs)
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

        # --- TOP TEXT (SIZE 6) ---
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
        time.sleep(8) 

        # --- BOTTOM TEXT (SIZE 10) ---
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
            print("No new image found.")
