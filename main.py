import Papa
import database
import time

if __name__ == "__main__":
    conn = database.init_db()

    url = Papa.START_URL
    while url:
        soup = Papa.fetch_page(url)
        if soup:
            demon_links = Papa.extract_demons(soup)
            print(f"Found {len(demon_links)} demons on this page.")
            for name, demon_url in demon_links:
                print(f"{name}: {demon_url}")
                try:
                    demon_soup = Papa.fetch_page(demon_url)
                    if demon_soup:
                        demon_data = Papa.extract_demon_info(demon_soup, name, demon_url)
                        database.insert_demon_data(conn, demon_data)
                except Exception as e:
                    with open("scraper_errors.log", "a", encoding="utf-8") as f:
                        f.write(f"{name} | {demon_url} | {str(e)}\n")
            next_url = Papa.find_next_page(soup)
            if next_url:
                url = next_url
                time.sleep(2)  # Throttle
            else:
                print("No next page found, stopping")
                break