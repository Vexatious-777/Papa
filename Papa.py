# Heavily commented for learning purposes
import requests # imports the Library for HTTP requests (GET/POST)
from bs4 import BeautifulSoup # imports the beatifulsoup parser and DOM navigator
import time # imports the library for time delay to ensure we don't overload the site
import database
import os
import requests

BASE_URL = "https://megatenwiki.com" # what it says on the tin; the base url that other parts will build upon
START_URL = f"{BASE_URL}/wiki/Category:Demons_in_Shin_Megami_Tensei_(Game)" # also what it says on the tin

# it was suggested to use a fake user-agent to mimic a browser to avoid common python protection ploys
HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; WebScraper/1.0; https://yourdomain.com/bot)"
}

# function to fetch a page
def fetch_page(url):
    """Make an HTTP GET request and return the BeautifulSoup object"""
    response = requests.get(url, headers=HEADERS) # sends the HTTP request to get the HTML (web address, Hyper Text Markup Language)
    if response.status_code == 200: # 200 means succesful
        return BeautifulSoup(response.text, "html.parser") # and if succesful actually enacts the parser
    else:
        print(f"Failed to load page: {url}") # Error message
        return None # The scariest message: nothing at all

def extract_demons(soup):
    """Extracts all demon name/title pairs and hrefs from the category page."""
    demon_links = []
    for a in soup.select("div.mw-category a"): # CSS selector to get all <a> tags inside the category block
        title = a.get("title") # extracts the title demon name
        href = a.get("href")  # extracts the demons web link "relative URL"
        if title == "Demons in Shin Megami Tensei": # should skip the opening link whick leads to another wiki page
            continue
        if title and href:  # if a matching title and link are found.... 
            demon_links.append((title, BASE_URL + href)) #.... they are appended and added to the demon links list
    return demon_links  # returns a list of tuples (title, full_url)

def find_next_page(soup):
    """Finds the URl for the next page in the category listing, if it exsists."""
    next_link = soup.find("a", string="next page")
    if next_link:
        next_url = BASE_URL + next_link.get("href")
        print(f"Found next page: {next_url}")
        return next_url
    else:
        print("No next page found. Scraping Complete")
        return None
    
def download_image(image_url, demon_name, save_folder="images"):
    """
    Downloads the image from image_url and saves it under save_folder
    with a filename based on demon_name for clarity.
    """
    if not os.path.exists(save_folder):
        os.makedirs(save_folder)

    # Clean demon_name for filesystem safety
    safe_name = demon_name.replace(" ", "_").replace("/", "_")
    file_extension = os.path.splitext(image_url)[1].split("?")[0]  # get .png, .jpg
    filename = f"{safe_name}{file_extension}"
    filepath = os.path.join(save_folder, filename)

    # Avoid re-downloading if already exists
    if os.path.exists(filepath):
        print(f"[SKIP] {filename} already exists.")
        return filepath

    try:
        response = requests.get(image_url, headers=HEADERS, stream=True, timeout=10)
        response.raise_for_status()
        with open(filepath, "wb") as f:
            for chunk in response.iter_content(8192):
                f.write(chunk)
        print(f"[DOWNLOADED] {filename}")
        return filepath
    except Exception as e:
        print(f"[ERROR] Failed to download {image_url}: {e}")
        return None
    
def extract_main_image_highres(soup):
    """
    Extracts the high-resolution demon image URL from a megatenwiki demon page.
    Prioritizes 600px if available, falls back to 300px, returns 'No image found.' if absent.
    """
    # Locate the first relevant <img> tag (typically in infobox or page content)
    image_tag = soup.find("img", class_="pi-image-thumbnail")
    if image_tag:
        # Prefer 600px if available in srcset
        srcset = image_tag.get("srcset", "")
        highres_url = ""
        if srcset:
            # srcset format:
            # "/images/.../300px-....png 1x, /images/.../600px-....png 2x"
            parts = srcset.split(",")
            if len(parts) > 1:
                highres_part = parts[1].strip().split(" ")[0]  # second URL before ' 2x'
                highres_url = highres_part

        # Fallback to src attribute if no high-res found
        if not highres_url:
            highres_url = image_tag.get("src", "")

        # Normalize URL (handle relative URLs)
        if highres_url.startswith("//"):
            highres_url = "https:" + highres_url
        elif highres_url.startswith("/"):
            highres_url = BASE_URL + highres_url

        return highres_url

    return "No image found."
    
def extract_demon_info(soup, name, url):
    """Extracts demon details from an individual demon page"""
    image_url = None
    infobox = soup.find("table", class_="infobox")
    if infobox:
        img_tag = infobox.find("img")
        if img_tag:
            image_url = BASE_URL + img_tag.get("src") if img_tag.get("src").startswith("/") else img_tag.get("src")

    image_url = extract_main_image_highres(soup)

    local_image_path = None
    if image_url != "No image found.":
        local_image_path = download_image(image_url, name)

    # Extract Origin paragraph
    origin_paragraph = ""
    origin_span = soup.find("span", id="Origin")
    if origin_span:
        parent = origin_span.find_parent()
        next_p = parent.find_next_sibling("p")
        if next_p:
            origin_paragraph = next_p.get_text(strip=True)

    # Extract Race (Shin Megami Tensei only)
    race = ""
    if infobox:
        for row in infobox.find_all("tr"):
            header = row.find("th")
            if header and "Race" in header.text:
                td = row.find("td")
                if td:
                    # Check each text chunk, keep only SMT1
                    for a_tag in td.find_all("a"):
                        sibling = a_tag.find_next_sibling()
                        if sibling and sibling.name == "span" and "tooltiptext" in sibling.get("class",[]):
                            if "Shin Megami Tensei" in sibling.get_text():
                                race = a_tag.get_text(strip=True)
                                break
                break

    # Extract Alignment
    alignment = ""
    if infobox:
        for row in infobox.find_all("tr"):
            header = row.find("th")
            if header and "Alignment" in header.text:
                td = row.find("td")
                if td:
                    for a_tag in td.find_all("a"):
                        sibling = a_tag.find_next_sibling()
                        if sibling and sibling.name == "span" and "tooltiptext" in sibling.get("class", []):
                            if "Shin Megami Tensei" in sibling.get_text():
                                alignment = a_tag.get_text(strip=True)
                                break
                    if not alignment:
                        #Fallback if no tooltips, join all stripped strings
                        alignment = " ".join(td.stripped_strings)
                break

    return {
        "name": name,
        "url": url,
        "image_url": image_url,
        "local_image_path": local_image_path,
        "origin": origin_paragraph,
        "race": race,
        "alignment": alignment
    }

    
    
