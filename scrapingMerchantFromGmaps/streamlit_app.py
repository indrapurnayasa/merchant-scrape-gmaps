import streamlit as st
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
import pandas as pd
import time
import re

def setup_driver():
    options = Options()
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
        
        # Wait for initial results to load
        results = WebDriverWait(driver, 10).until(
            EC.presence_of_all_elements_located((By.CSS_SELECTOR, result_items_selector))
        )
        
        last_count = 0  # Keeps track of the previous number of results
        max_attempts = 20  # Set a reasonable limit to avoid infinite loops
        attempts = 0
        
        while attempts < max_attempts:
            driver.execute_script("arguments[0].scrollIntoView();", results[-1])
            time.sleep(2)  # Allow time for more results to load
            
            # Fetch new results after scrolling
            results = driver.find_elements(By.CSS_SELECTOR, result_items_selector)
            
            # Check if no new results are loaded
            if len(results) == last_count:
                attempts += 1
            else:
                attempts = 0  # Reset attempts if new results are found
            
            last_count = len(results)  # Update the count of results
        
        print(f"Total results found after scrolling: {len(results)}")
        return results

    except TimeoutException:
        print("Timeout while scrolling results.")
        return []
    except Exception as e:
        print(f"An error occurred while scrolling: {str(e)}")
        return []

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
        # Remove commas from the name
        name = name.replace(',', '')
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
        pass
        
    return {
        "name": name,
        "address": address,
        "phone": phone,
        "hours": hours
    }


def main():
    st.set_page_config(page_title="Google Maps Crawler", page_icon="🌍")
    st.title("Google Maps Business Crawler")
    
    # Initialize session state
    if "results_data" not in st.session_state:
        st.session_state.results_data = None

    # Search input
    query = st.text_input("Enter business name and location:")
    
    if st.button("Search"):
    driver = None  # Initialize the driver variable
    try:
        with st.spinner("Scraping Google Maps..."):
            driver = setup_driver()  # Assign the driver instance
            search_place(driver, query)
            
            # Scroll and fetch all results
            all_results = scroll_results(driver)
            
            # Initialize list to store results
            results_data = []
            
            progress_bar = st.progress(0)
            for idx, result in enumerate(all_results):
                driver.execute_script("arguments[0].scrollIntoView({block: 'start'});", result)
                time.sleep(1)
                result.click()
                time.sleep(2)
                details = get_place_details(driver)
                
                # Replace newline characters in "hours" with a delimiter
                if "hours" in details and isinstance(details["hours"], str):
                    details["hours"] = details["hours"].replace("\n", " | ")  # Replace newline with " | "
                
                results_data.append(details)
                
                # Update progress
                progress = (idx + 1) / len(all_results)
                progress_bar.progress(progress)
            
            # Save results in session state
            st.session_state.results_data = results_data

            # Display results
            st.write(f"Found {len(results_data)} results:")
            st.dataframe(pd.DataFrame(results_data))
            
    except Exception as e:
        st.error(f"An error occurred: {str(e)}")
    
    finally:
        if driver:  # Check if driver was initialized
            driver.quit()

    # Display results from session state if available
    if st.session_state.results_data:
        results_data = st.session_state.results_data
        df = pd.DataFrame(results_data)

        # Generate file name based on query
        sanitized_query = re.sub(r'[^\w\s]', '', query).strip().replace(' ', '_')
        file_name = f"{sanitized_query}_google_maps_results.csv"

        # Convert DataFrame to CSV
        csv = df.to_csv(index=False, encoding='utf-8', quoting=1).encode('utf-8')

        # Display results
        st.write("Results:")
        st.dataframe(df)

        # Add download button
        st.download_button(
            label="Download results as CSV",
            data=csv,
            file_name=file_name,
            mime="text/csv"
        )

if __name__ == "__main__":
    main()
