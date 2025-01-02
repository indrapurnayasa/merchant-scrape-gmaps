from scrapingGmaps import GoogleMapsScraper
import time

def main():
    scraper = GoogleMapsScraper()
    try:
        # Search for the place
        place = "Fore Coffee Jakarta Pusat"
        if scraper.search_place(place):
            # Process all results
            all_details = scraper.process_all_results()
            
            # Print all collected details
            print("\nAll collected place details:")
            for i, (name, address, website) in enumerate(all_details, 1):
                print(f"\n{i}. {name}")
                print(f"Address: {address}")
                print(f"Website: {website}")
                print("-" * 50)
            
            print(f"\nTotal unique places processed: {len(all_details)}")
            print(f"Total unique names found: {len(scraper.processed_names)}")
            
    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        scraper.close()

if __name__ == "__main__":
    main()