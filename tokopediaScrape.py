from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup

# Set up Selenium with Chrome
options = Options()
options.headless = True  # Run in headless mode to avoid opening a browser window
service = Service(ChromeDriverManager().install())
driver = webdriver.Chrome(service=service, options=options)

# Define the URL of the category page you want to scrape
url = 'https://www.tokopedia.com/p/audio-kamera-elektronik-lainnya/audio'  # Replace with the actual category URL

# Navigate to the Tokopedia category page
driver.get(url)

# Allow time for JavaScript to load
driver.implicitly_wait(10)

# Get the page source and parse with BeautifulSoup
page_source = driver.page_source
soup = BeautifulSoup(page_source, 'html.parser')

# Find all product containers
product_containers = soup.find_all('div', class_='css-11s9vse')

# Extract and print merchant and product details
for container in product_containers:
    product_name = container.find('span', class_='css-20kt3o').text
    ywdpwd_elements = container.find_all('span', class_='css-ywdpwd')
    location = ywdpwd_elements[0].text if len(ywdpwd_elements) > 0 else 'N/A'
    merchant_name = ywdpwd_elements[1].text if len(ywdpwd_elements) > 1 else 'N/A'
    
    print(f'Product Name: {product_name}')
    print(f'Location: {location}')
    print(f'Merchant Name: {merchant_name}')
    print('---')

# Close the browser
driver.quit()
