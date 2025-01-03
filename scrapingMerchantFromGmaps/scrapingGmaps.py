from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import time
import re

def setup_driver():
    options = webdriver.ChromeOptions()
    options.add_argument('--start-maximized')
    options.add_argument('--headless')
    return webdriver.Chrome(options=options)

def search_place(driver, query):
    driver.get("https://www.google.com/maps")
    search_box = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.ID, "searchboxinput"))
    )
    search_box.send_keys(query)
    search_box.send_keys(Keys.ENTER)
    time.sleep(3)

def format_opening_hours(hours_text):
    if hours_text == "N/A":
        return "N/A"
    
    # Day name mapping
    day_mapping = {
        'Senin': 'Monday',
        'Selasa': 'Tuesday',
        'Rabu': 'Wednesday',
        'Kamis': 'Thursday',
        'Jumat': 'Friday',
        'Sabtu': 'Saturday',
        'Minggu': 'Sunday'
    }
    
    # Desired order of days
    day_order = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday']
    
    # Handle the condition where the business has no hours (e.g., "Hide open hours for the week")
    # if "Hide open hours for the week" in hours_text or "Jam buka dapat berbeda" in hours_text:
    #     return "N/A"
    
    # Handle if "Open 24 hours" is found in the text
    if "Open 24 hours" in hours_text:
        return "Open 24 hours every day."
    
    # Remove non-relevant phrases
    hours_text = hours_text.replace("Sembunyikan jam buka untuk seminggu", "").replace("Jam buka dapat berbeda", "*")
    days = hours_text.split(';')
    formatted_hours = []
    
    for day in days:
        if not day.strip():
            continue
            
        parts = day.strip().split(',')
        if len(parts) < 2:
            continue
            
        day_part = parts[0].split('(')[0].strip()
        day_part = day_mapping.get(day_part, day_part)
        time_part = parts[1].strip()
        
        # Check if "Open 24 hours" is in the time part
        if "Open 24 hours" in time_part:
            formatted_hours.append(f"{day_part}: Open 24 hours")
            continue
        
        # Otherwise, proceed with regular time formatting
        time_parts = time_part.split('hingga')
        if len(time_parts) == 2:
            start_time = time_parts[0].strip().replace(':', '').replace('.', '')
            end_time = time_parts[1].strip().replace(':', '').replace('.', '')
            
            start_hour = int(start_time[:2])
            end_hour = int(end_time[:2])
            
            if end_hour >= 24:
                end_hour = end_hour - 24
                next_day = " (close tomorrow)"
            else:
                next_day = ""
                
            formatted_start = f"{start_hour:02d}:00"
            formatted_end = f"{end_hour:02d}:00"
            
            special_note = "" if day_part == "Wednesday" else (" *" if '*' in parts[-1] else "")
            formatted_hours.append(f"{day_part}: {formatted_start} until {formatted_end}{next_day}{special_note}")
    
    # Sort the hours based on the desired day order
    formatted_hours.sort(key=lambda x: day_order.index(x.split(':')[0]))
    
    return "\n".join(formatted_hours)

def scroll_results(driver):
    try:
        result_items_selector = ".Nv2PK"
        results = WebDriverWait(driver, 10).until(
            EC.presence_of_all_elements_located((By.CSS_SELECTOR, result_items_selector))
        )
        
        if not results:
            print("No results found to scroll.")
            return False
        
        last_count = len(results)
        while True:
            results[-1].location_once_scrolled_into_view
            time.sleep(2)
            
            results = driver.find_elements(By.CSS_SELECTOR, result_items_selector)
            if len(results) == last_count:
                break
            last_count = len(results)
        
        print(f"Scrolled through {len(results)} results.")
        return True

    except TimeoutException:
        print("Timeout while scrolling results.")
        return False

def get_phone_number(driver):
    try:
        elements = driver.find_elements(By.CSS_SELECTOR, "div.AeaXub div.rogA2c div.Io6YTe")
        for element in elements:
            text = element.text.strip()
            
            # Check if text contains any digit and a hyphen (phone-like pattern)
            if any(char.isdigit() for char in text) and '-' in text:
                
                # Check if the text contains any address-like keywords
                if any(keyword in text.lower() for keyword in ['jl', 'jalan', 'ruko', 'komplek', 'rt', 'rw', 'gang', 'gg', 'desa', 'kelurahan', 'kecamatan']):
                    return "N/A"
                
                # If the text is valid (it's a phone number)
                return text.replace('-', '')
        return "N/A"
    except:
        return "N/A"

def get_place_details(driver):
    try:
        name = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, "DUwDvf"))
        ).text
    except:
        name = "N/A"
        
    try:
        address_elements = driver.find_elements(By.CSS_SELECTOR, "div.Io6YTe.fontBodyMedium.kR99db.fdkmkc")
        address = next((elem.text for elem in address_elements
                        if any(keyword in elem.text.lower() for keyword in ['jl', 'jalan', 'ruko', 'komplek', 'rt', 'rw', 'gang', 'gg', 'desa', 'kelurahan', 'kecamatan']) 
                        and not re.search(r'\d{2,5}[-\s]?\d{2,5}[-\s]?\d{2,5}', elem.text)), "N/A")
    except:
        address = "N/A"
    
    phone = get_phone_number(driver)

    # Initialize `hours` with a default value
    hours = "N/A"
    try:
        temporarily_closed_element = driver.find_elements(By.CSS_SELECTOR, "div.o0Svhf span.aSftqf")
        if temporarily_closed_element:
            for element in temporarily_closed_element:
                if "Temporarily closed" in element.text.strip():
                    hours = "Temporarily Closed"
                    break
        else:
            # Attempt to extract hours if not temporarily closed
            hours_raw = driver.find_element(By.CSS_SELECTOR, "div.t39EBf.GUrTXd").get_attribute("aria-label")
            if hours_raw:  # Ensure `hours_raw` is not None or empty
                hours = format_opening_hours(hours_raw)
    except:
        # If anything fails, hours will remain as "N/A"
        pass
        
    return {
        "name": name,
        "address": address,
        "phone": phone,
        "hours": hours
    }

def main():
    driver = setup_driver()
    query = ("Fore Coffee Jakarta Pusat")
    
    try:
        search_place(driver, query)
        has_results = scroll_results(driver)
        
        if has_results:
            results = driver.find_elements(By.CLASS_NAME, "Nv2PK")
            
            for result in results:
                driver.execute_script("arguments[0].scrollIntoView({block: 'start'});", result)
                time.sleep(1)
                result.click()
                time.sleep(2)
                details = get_place_details(driver)
                print("Place Details:")
                print(f"Name: {details['name']}")
                print(f"Address: {details['address']}")
                print(f"Phone Number: {details['phone']}")
                print(f"Opening Hours:")
                print(details['hours'])
                print("-" * 50)
        else:
            details = get_place_details(driver)
            print("Place Details:")
            print(f"Name: {details['name']}")
            print(f"Address: {details['address']}")
            print(f"Phone Numbers: {details['phone']}")
            print(f"Opening Hours:")
            print(details['hours'])
            
    finally:
        driver.quit()

if __name__ == "__main__":
    main()
