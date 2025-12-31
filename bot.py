import os, requests, time, random, json
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright

# --- Configuration ---
HISTORY_FILE = "posted_urls.txt"
PORN_SOURCE = "https://www.pornpics.com/tags/pussy-fuck/"
THREAD_REPLY_URL = "https://exforum.live/threads/fucking-pussy-collection.203456/reply"

# 1. Professional/General Fillers (No Desi words)
TOP_FILLERS = [
    "Full gallery available at:", "Check out more updates:", "Latest collection here:", 
    "View the full set at:", "New updates posted on:", "Direct access to gallery:",
    "Explore more content at:", "Get full access here:", "See more updates on:",
    "Full high-res gallery at:", "More exclusive content here:", "Access the complete set:",
    "Daily updates posted on:", "Premium gallery available at:", "Source and full set:",
    "Find more highlights at:", "Check the full collection on:", "Complete gallery link:",
    "Official updates available here:", "Direct link to the collection:", "Full set uploaded at:",
    "Click for more updates:", "Browse the full gallery on:", "Discover more content at:",
    "Find the hidden gems here:", "Exclusive highlights posted on:", "Get the full experience at:",
    "More high-quality sets on:", "Updated gallery link:", "Direct source available at:",
    "Stay updated via:", "New sets added on:", "Check this out at:"
]

# 2. Bottom General Phrases (No Desi words, No Link repetition)
BOTTOM_PHRASES = [
    "Stay tuned for daily updates! 🔥", "More high-quality content coming soon.", 
    "Don't miss the next collection! 🔞", "Premium quality images updated regularly.", 
    "Check back later for more updates. 💦", "Full high-res collection available on site.",
    "Follow for more exclusive updates! 🍑", "Fresh content added every hour. 🔥",
    "Enjoy the high-quality resolution! 📸", "Top-tier content coming your way every day.",
    "Only the best sets for this community. 💯", "Crystal clear quality for your viewing pleasure.",
    "Bookmark this thread for more upcoming sets.", "Check back tomorrow for the next part.",
    "More from this collection will be posted shortly.", "Continuous updates throughout the week.",
    "Hope you guys enjoy this new addition! ✨", "Don't forget to check our daily feed.",
    "Always bringing the latest high-res sets to you.", "Stay connected for more exclusive uploads.",
    "Quality over quantity, as always! 💎", "More premium shots are being processed now.",
    "The next update is going to be even better. 🔥", "Keeping the gallery fresh with daily uploads.",
    "High-resolution content is our priority. 🌟", "Don't miss out on the upcoming part of this set.",
    "More exclusive highlights arriving soon! 🔞", "Direct source for high-quality sets."
]

# 3. Domain Obfuscation Variants
CAPTION_VARIANTS = [
    "freepornx [dot] site", "freepornx {dot} site", "freepornx (dot) site",
    "freepornx | site", "f r e e p o r n x . s i t e", "f\u200Breepornx\u200B.\u200Bsite",
    "freepornx [.] site", "freepornx ( . ) site", "freepornx / site",
    "FreePornX.Site", "freepornx DOT site", "freepornx * site",
    "freepornx ~ site", "freepornx ::: site", "f.r.e.e.p.o.r.n.x.s.i.t.e",
    "freepornx @ site", "freepornx_site", "FrEePoRnX.SiTe",
    "f-r-e-e-p-o-r-n-x-site", "freepornx [at] site", "freepornx [d-o-t] site", 
    "freepornx ( . ) s i t e", "freepornx...site", "freepornx /// site", 
    "freepornx -- site", "freepornx [[dot]] site", "freepornx <dot> site",
    "freepornx [point] site", "freepornx (period) site", "freepornx !!! site",
    "freepornx +++ site", "freepornx === site", "freepornx >>> site",
    "freepornx [ d o t ] s i t e", "freepornx [at] s-i-t-e", "freepornx |-| site"
]

def get_new_image():
    print(f"--- Step 1: Scraping Image from {PORN_SOURCE} ---")
    headers = {'User-Agent': 'Mozilla/5.0'}
    try:
        r = requests.get(PORN_SOURCE, headers=headers, timeout=30)
        soup = BeautifulSoup(r.text, 'html.parser')
        links = [a['href'] for a in soup.find_all('a', href=True) if "/galleries/" in a['href']]
        if not links: return None
        
        target_gal = random.choice(links)
        target_gal = target_gal if target_gal.startswith('http') else "https://www.pornpics.com" + target_gal
        
        r_gal = requests.get(target_gal, headers=headers, timeout=30)
        gal_soup = BeautifulSoup(r_gal.text, 'html.parser')
        
        posted = open(HISTORY_FILE, "r").read().splitlines() if os.path.exists(HISTORY_FILE) else []
        valid_imgs = [img.get('data-src') or img.get('src') for img in gal_soup.find_all('img') if "pornpics.com" in (img.get('data-src') or img.get('src', ''))]
        
        new_imgs = [u if u.startswith('http') else "https:" + u for u in valid_imgs if u not in posted]
        if new_imgs:
            img_url = random.choice(new_imgs)
            print(f"SUCCESS: Image Found -> {img_url}")
            with open(HISTORY_FILE, "a") as f: f.write(img_url + "\n")
            return img_url
        return None
    except Exception as e:
        print(f"Scrape Error: {e}"); return None

def post_to_forum(p, direct_url):
    # Random selection for each post
    selected_top_filler = random.choice(TOP_FILLERS)
    selected_variant = random.choice(CAPTION_VARIANTS)
    selected_bottom_phrase = random.choice(BOTTOM_PHRASES)

    print(f"--- Step 2: Posting with Randomization ---")
    print(f"Top: {selected_top_filler} {selected_variant}")
    print(f"Bottom: {selected_bottom_phrase}")

    browser = p.chromium.launch(headless=True, args=["--no-sandbox"])
    context = browser.new_context(user_agent="Mozilla/5.0")
    
    cookies_raw = os.environ.get('EX_COOKIES')
    if not cookies_raw: return
    context.add_cookies(json.loads(cookies_raw))
    
    page = context.new_page()
    page.set_default_timeout(90000)
    
    try:
        page.goto(THREAD_REPLY_URL, wait_until="networkidle")
        editor = page.locator('.fr-element').first
        editor.wait_for(state="visible")

        # --- TOP TEXT ---
        editor.focus()
        page.keyboard.type(f"[SIZE=6][B]{selected_top_filler} {selected_variant}[/B][/SIZE]\n")
        time.sleep(2)

        # 1. Click Image Button
        page.click('#insertImage-1', force=True)
        time.sleep(3)

        # 2. Click 'By URL' Tab
        page.locator('button[data-cmd="imageByURL"], .fr-popup button[data-cmd="imageByURL"]').first.click(force=True)
        time.sleep(2)

        # 3. Fill URL
        url_input = page.locator('input[name="src"], .fr-image-by-url-layer input[type="text"]').first
        url_input.wait_for(state="visible", timeout=20000)
        url_input.fill(direct_url)
        page.keyboard.press("Enter")
        time.sleep(8) 

        # --- BOTTOM TEXT ---
        editor.focus()
        page.keyboard.press("Control+End")
        page.keyboard.type(f"\n[SIZE=7][B]{selected_bottom_phrase}[/B][/SIZE]")
        time.sleep(2)

        # 4. Final Post
        submit_btn = page.locator('button:has-text("Post reply"), .button--icon--reply').first
        submit_btn.click()
        
        page.wait_for_timeout(10000)
        print("--- TASK COMPLETED ---")
        
    except Exception as e:
        print(f"Forum Error: {e}")
    finally:
        browser.close()

if __name__ == "__main__":
    with sync_playwright() as playwright:
        img_url = get_new_image()
        if img_url:
            post_to_forum(playwright, img_url)
