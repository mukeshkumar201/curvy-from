import os, requests, time, random, json, io
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright
from PIL import Image, ImageDraw, ImageFont

# --- Configuration ---
HISTORY_FILE = "posted_urls.txt"
PORN_SOURCE = "https://www.pornpics.com/tags/pussy-fuck/"
THREAD_REPLY_URL = "https://exforum.live/threads/fucking-pussy-collection.203456/reply"

# GitHub Secrets se values uthayega
IMGBB_API_KEY = os.environ.get('IMGBB_API_KEY')
EX_COOKIES = os.environ.get('EX_COOKIES')

def add_watermark(image_bytes):
    """Image par 'freepornx.site' ka watermark lagayega"""
    try:
        img = Image.open(io.BytesIO(image_bytes))
        if img.mode != 'RGB':
            img = img.convert('RGB')
        
        draw = ImageDraw.Draw(img)
        width, height = img.size
        font_size = int(width * 0.05)
        
        try:
            # GitHub Actions (Linux) default font path
            font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", font_size)
        except:
            font = ImageFont.load_default()

        text = "freepornx.site"
        bbox = draw.textbbox((0, 0), text, font=font)
        tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
        x, y = width - tw - 20, height - th - 20

        # Shadow (Black) aur Main Text (White)
        draw.text((x+2, y+2), text, font=font, fill="black")
        draw.text((x, y), text, font=font, fill="white")

        img_io = io.BytesIO()
        img.save(img_io, format='JPEG', quality=95)
        return img_io.getvalue()
    except Exception as e:
        print(f"Pillow Error: {e}")
        return None

def upload_to_imgbb(img_bytes):
    """ImgBB par image upload karke direct link return karega"""
    if not IMGBB_API_KEY:
        print("Error: IMGBB_API_KEY Secret missing!")
        return None
    
    print("--- Step 3: Uploading to ImgBB ---")
    api_url = "https://api.imgbb.com/1/upload"
    # ImgBB API parameters
    payload = {
        "key": IMGBB_API_KEY,
        "expiration": "0" # 0 matlab permanent (delete nahi hogi)
    }
    # Image file ko bhej rahe hain
    files = {"image": ("image.jpg", img_bytes, "image/jpeg")}
    
    try:
        r = requests.post(api_url, data=payload, files=files)
        res = r.json()
        if res.get("status") == 200:
            link = res["data"]["url"]
            print(f"SUCCESS: Hosted Link -> {link}")
            return link
        else:
            print(f"Upload Failed: {res}")
            return None
    except Exception as e:
        print(f"ImgBB API Error: {e}")
        return None

def get_processed_image():
    """Scraping, Watermarking and Hosting logic"""
    print(f"--- Step 1: Scraping from {PORN_SOURCE} ---")
    headers = {'User-Agent': 'Mozilla/5.0'}
    try:
        r = requests.get(PORN_SOURCE, headers=headers)
        soup = BeautifulSoup(r.text, 'html.parser')
        gal_links = [a['href'] for a in soup.find_all('a', href=True) if "/galleries/" in a['href']]
        
        target = random.choice(gal_links)
        if not target.startswith('http'): target = "https://www.pornpics.com" + target

        r_gal = requests.get(target, headers=headers)
        gal_soup = BeautifulSoup(r_gal.text, 'html.parser')
        posted = open(HISTORY_FILE, "r").read().splitlines() if os.path.exists(HISTORY_FILE) else []
        
        valid_imgs = []
        for img in gal_soup.find_all('img'):
            src = img.get('data-src') or img.get('src', '')
            if "pornpics.com" in src and any(ext in src.lower() for ext in ['.jpg', '.jpeg', '.png']):
                if "google-icon" not in src and "logo" not in src.lower():
                    valid_imgs.append(src)
        
        new_imgs = [u if u.startswith('http') else "https:" + u for u in valid_imgs if u not in posted]
        
        if new_imgs:
            selected = random.choice(new_imgs)
            print(f"Found Image: {selected}")
            img_raw = requests.get(selected).content
            marked = add_watermark(img_raw)
            if marked:
                final_link = upload_to_imgbb(marked)
                if final_link:
                    with open(HISTORY_FILE, "a") as f: f.write(selected + "\n")
                    return final_link
        return None
    except Exception as e:
        print(f"Scrape Error: {e}"); return None

def post_to_forum(p, hosted_url):
    """Forum par BBCode post karega"""
    print("--- Step 4: Posting to Forum ---")
    browser = p.chromium.launch(headless=True, args=["--no-sandbox"])
    context = browser.new_context(user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")
    
    try:
        context.add_cookies(json.loads(EX_COOKIES))
    except:
        print("CRITICAL: Cookie JSON format galat hai!"); return

    page = context.new_page()
    try:
        page.goto(THREAD_REPLY_URL, wait_until="domcontentloaded", timeout=60000)
        
        if page.locator('a[href*="logout"]').count() == 0:
            print("CRITICAL: Login Failed! Fresh Cookies Required.")
            return

        editor = page.locator('.fr-element').first
        editor.wait_for(state="visible", timeout=30000)
        
        editor.focus()
        page.keyboard.type(f"[IMG]{hosted_url}[/IMG]")
        time.sleep(3)
        
        page.locator('button:has-text("Post reply"), .button--icon--reply').first.click()
        page.wait_for_timeout(5000)
        print("--- SUCCESS: IMAGE POSTED ---")
    except Exception as e: print(f"Forum Error: {e}")
    finally: browser.close()

if __name__ == "__main__":
    with sync_playwright() as playwright:
        link = get_processed_image()
        if link: post_to_forum(playwright, link)
