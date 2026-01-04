import os, requests, time, random, json, io
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright
from PIL import Image, ImageDraw, ImageFont

# --- Configuration ---
HISTORY_FILE = "posted_urls.txt"
PORN_SOURCE = "https://www.pornpics.com/tags/pussy-fuck/"
THREAD_REPLY_URL = "https://exforum.live/threads/fucking-pussy-collection.203456/reply"

# GitHub Secrets se values uthayega
FREEIMAGE_API_KEY = os.environ.get('FREEIMAGE_API_KEY')
EX_COOKIES = os.environ.get('EX_COOKIES')

def add_watermark(image_bytes):
    """Image par 'freepornx.site' ka watermark add karega"""
    print("--- Step 2: Adding Watermark ---")
    img = Image.open(io.BytesIO(image_bytes))
    if img.mode != 'RGB':
        img = img.convert('RGB')
    
    draw = ImageDraw.Draw(img)
    width, height = img.size
    font_size = int(width * 0.05) # responsive size
    
    try:
        # GitHub Linux environments ke liye default font path
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", font_size)
    except:
        font = ImageFont.load_default()

    text = "freepornx.site"
    bbox = draw.textbbox((0, 0), text, font=font)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    
    # Bottom-right position
    x, y = width - tw - 20, height - th - 20

    # Draw Shadow (Black) and Text (White)
    draw.text((x+2, y+2), text, font=font, fill="black")
    draw.text((x, y), text, font=font, fill="white")

    img_io = io.BytesIO()
    img.save(img_io, format='JPEG', quality=95)
    return img_io.getvalue()

def upload_to_freeimage(img_bytes):
    """Freeimage.host par upload karke direct link return karega"""
    if not FREEIMAGE_API_KEY:
        print("Error: FREEIMAGE_API_KEY Secret missing!")
        return None
        
    print("--- Step 3: Uploading to Freeimage.host ---")
    api_url = "https://freeimage.host/api/1/upload"
    payload = {"key": FREEIMAGE_API_KEY, "action": "upload", "format": "json"}
    files = {"source": ("image.jpg", img_bytes, "image/jpeg")}

    try:
        r = requests.post(api_url, data=payload, files=files)
        res = r.json()
        if res.get("status_code") == 200:
            return res["image"]["url"]
        return None
    except Exception as e:
        print(f"Upload Error: {e}"); return None

def get_processed_image():
    """Pornpics se image nikal kar process karega"""
    print(f"--- Step 1: Scraping from {PORN_SOURCE} ---")
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
    try:
        r = requests.get(PORN_SOURCE, headers=headers)
        soup = BeautifulSoup(r.text, 'html.parser')
        gal_links = [a['href'] for a in soup.find_all('a', href=True) if "/galleries/" in a['href']]
        
        target = random.choice(gal_links)
        if not target.startswith('http'): 
            target = "https://www.pornpics.com" + target

        r_gal = requests.get(target, headers=headers)
        gal_soup = BeautifulSoup(r_gal.text, 'html.parser')
        
        posted = open(HISTORY_FILE, "r").read().splitlines() if os.path.exists(HISTORY_FILE) else []
        
        imgs = [img.get('data-src') or img.get('src') for img in gal_soup.find_all('img') if "pornpics.com" in (img.get('data-src') or img.get('src', ''))]
        new_imgs = [u if u.startswith('http') else "https:" + u for u in imgs if u not in posted]
        
        if new_imgs:
            selected_url = random.choice(new_imgs)
            print(f"Processing Image: {selected_url}")
            
            img_raw = requests.get(selected_url).content
            marked_img = add_watermark(img_raw)
            final_link = upload_to_freeimage(marked_img)
            
            if final_link:
                with open(HISTORY_FILE, "a") as f: 
                    f.write(selected_url + "\n")
                return final_link
        return None
    except Exception as e:
        print(f"Scrape Error: {e}"); return None

def post_to_forum(p, hosted_url):
    """BBCode format mein post karega"""
    print("--- Step 4: Posting to Forum via BBCode ---")
    browser = p.chromium.launch(headless=True)
    context = browser.new_context(user_agent="Mozilla/5.0")
    
    if not EX_COOKIES:
        print("Error: EX_COOKIES Secret missing!")
        return
        
    context.add_cookies(json.loads(EX_COOKIES))
    page = context.new_page()
    
    try:
        page.goto(THREAD_REPLY_URL, wait_until="networkidle")
        editor = page.locator('.fr-element').first
        editor.wait_for(state="visible")
        
        # Editor mein BBCode type karega [IMG]link[/IMG]
        editor.focus()
        page.keyboard.type(f"[IMG]{hosted_url}[/IMG]")
        
        time.sleep(3) # Wait to ensure text is registered
        
        # Submit the post
        page.locator('button:has-text("Post reply"), .button--icon--reply').first.click()
        print("--- SUCCESS: POSTED SUCCESSFULLY ---")
    except Exception as e:
        print(f"Forum Error: {e}")
    finally:
        browser.close()

if __name__ == "__main__":
    with sync_playwright() as playwright:
        image_link = get_processed_image()
        if image_link:
            post_to_forum(playwright, image_link)
        else:
            print("Failed to get or process image.")
