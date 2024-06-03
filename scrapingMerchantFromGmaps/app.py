from scrapingGmaps import GoogleMapsScraper
import time

if __name__ == "__main__":
    # Initialize the scraper
    scraper = GoogleMapsScraper()

    # Search for the place
    place = "waterboom kalimantan selatan"
    scraper.search_place(place)

    # Get search results
    results = scraper.get_search_results()

    # Iterate over each search result and get details
    for result in results:
        # Click on the search result
        result.click()
        time.sleep(5)  # Wait for the place details to load

        # Get place details
        try:
            name, address, website, latitude, longitude = scraper.get_place_details()
            print("Name:", name)
            print("Address:", address)
            print("Website:", website)
            print("Latitude:", latitude)
            print("Longitude:", longitude)
        except Exception as e:
            print("Error getting details for a place:", e)

        # Go back to the search results
        scraper.driver.execute_script("window.history.go(-1)")
        time.sleep(5)  # Wait for the search results to load

    # Close the scraper
    scraper.close()
