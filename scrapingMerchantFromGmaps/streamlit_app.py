import streamlit as st
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
import pandas as pd
import time
import re
import os

def setup_driver():
    """Configure Chrome WebDriver with deployment-ready options"""
    options = Options()
    options.add_argument('--start-maximized')
    options.add_argument('--headless')
    options.add_argument('--disable-gpu')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    
    # Handle both local development and cloud deployment
    if os.environ.get('GOOGLE_CHROME_BIN'):
        options.binary_location = os.environ.get('GOOGLE_CHROME_BIN')
    
    # Set up Chrome WebDriver service
    if os.environ.get('CHROMEDRIVER_PATH'):
        service = Service(executable_path=os.environ.get('CHROMEDRIVER_PATH'))
    else:
        service = Service()
    
    return webdriver.Chrome(service=service, options=options)

@st.cache_data(show_spinner=False)
def convert_df_to_csv(df):
    """Convert DataFrame to CSV with caching"""
    return df.to_csv(index=False, encoding='utf-8', quoting=1).encode('utf-8')

def main():
    # Page configuration
    st.set_page_config(
        page_title="Google Maps Business Crawler",
        page_icon="🌍",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # Add CSS for better UI
    st.markdown("""
        <style>
        .stProgress > div > div > div > div {
            background-color: #1f77b4;
        }
        .stDownloadButton {
            width: 100%;
        }
        </style>
    """, unsafe_allow_html=True)
    
    st.title("Google Maps Business Crawler")
    
    # Initialize session state
    if "results_data" not in st.session_state:
        st.session_state.results_data = None
    
    # Create two columns for input
    col1, col2 = st.columns([3, 1])
    
    with col1:
        query = st.text_input("Enter business name and location:", 
                            help="Example: Restaurants in Jakarta")
    
    with col2:
        search_button = st.button("🔍 Search", use_container_width=True)
    
    if search_button and query:
        driver = None
        try:
            with st.spinner("🔄 Initializing search..."):
                driver = setup_driver()
                
                # Your existing search_place function call
                search_place(driver, query)
                
                # Create a status container
                status_container = st.empty()
                status_container.info("📍 Scrolling through results...")
                
                # Get results
                all_results = scroll_results(driver)
                
                if not all_results:
                    st.warning("No results found. Please try a different search query.")
                    return
                
                # Initialize progress tracking
                progress_text = "Collecting business details..."
                my_bar = st.progress(0, text=progress_text)
                
                # Process results
                results_data = []
                for idx, result in enumerate(all_results):
                    try:
                        driver.execute_script("arguments[0].scrollIntoView({block: 'start'});", result)
                        time.sleep(1)
                        result.click()
                        time.sleep(2)
                        details = get_place_details(driver)
                        
                        if isinstance(details.get("hours"), str):
                            details["hours"] = details["hours"].replace("\n", " | ")
                        
                        results_data.append(details)
                        
                        # Update progress
                        progress = (idx + 1) / len(all_results)
                        my_bar.progress(progress, text=f"{progress_text} ({idx + 1}/{len(all_results)})")
                        
                    except Exception as e:
                        st.warning(f"Skipped one result due to error: {str(e)}")
                        continue
                
                # Store results in session state
                st.session_state.results_data = results_data
                
                # Clear progress bar and status
                my_bar.empty()
                status_container.empty()
                
                # Display results
                if results_data:
                    df = pd.DataFrame(results_data)
                    st.success(f"✅ Found {len(results_data)} results!")
                    
                    # Display dataframe with styling
                    st.dataframe(
                        df,
                        use_container_width=True,
                        height=400
                    )
                    
                    # Generate file name
                    sanitized_query = re.sub(r'[^\w\s]', '', query).strip().replace(' ', '_')
                    file_name = f"{sanitized_query}_google_maps_results.csv"
                    
                    # Add download button
                    csv = convert_df_to_csv(df)
                    st.download_button(
                        label="📥 Download Results as CSV",
                        data=csv,
                        file_name=file_name,
                        mime="text/csv",
                        key='download-csv'
                    )
                
        except Exception as e:
            st.error(f"❌ An error occurred: {str(e)}")
            
        finally:
            if driver:
                try:
                    driver.quit()
                except Exception as e:
                    st.warning(f"Error closing browser: {str(e)}")

if __name__ == "__main__":
    main()