from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from webdriver_manager.chrome import ChromeDriverManager
import time
from urllib.parse import urlparse

class GoogleMapsScraper:
    def __init__(self):
        self.driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()))

    def search_place(self, place):
        self.driver.get("https://www.google.com/maps")
        search_box = self.driver.find_element(By.ID, "searchboxinput")
        search_box.send_keys(place)
        search_box.send_keys(Keys.RETURN)
        time.sleep(5)  # Wait for the page to load results

    def get_search_results(self):
        results = self.driver.find_elements(By.XPATH, "//div[@class='Nv2PK THOPZb CpccDe']")
        return results

    def get_place_details(self):
        name_element = self.driver.find_element(By.XPATH, "//h1[contains(@class, 'DUwDvf')]")
        name = name_element.text

        address_element = self.driver.find_element(By.XPATH, "//div[contains(@class, 'Io6YTe')]")
        address = address_element.text

        # Find website element using XPath
        website_element = self.driver.find_element(By.XPATH, "//div[@class='rogA2c ITvuef']")

        # Check if website element is not None
        if website_element is not None:
            website = website_element.text
        else:
            website = None

        # Get the current URL
        current_url = self.driver.current_url

        # Parse the URL
        parsed_url = urlparse(current_url)

        # Get the latitude and longitude from the query parameters
        coordinates = parsed_url.path.split("@")[1].split(",")[0:2]
        latitude = coordinates[0]
        longitude = coordinates[1]

        return name, address, website, latitude, longitude

    def close(self):
        self.driver.quit()
