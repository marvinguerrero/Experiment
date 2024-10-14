import os
import asyncio
import pandas as pd
from pyppeteer import launch
from pyppeteer.errors import NetworkError, PageError

async def take_screenshots_and_check_accessibility(input_file, output_folder):
    print("Launching browser...")
    browser = await launch(headless=True, args=['--no-sandbox'])
    page = await browser.newPage()

    try:
        # Read URLs from the input file
        print("Reading URLs from input file...")
        with open(input_file, "r") as f:
            urls = f.readlines()
    except FileNotFoundError:
        print(f"Error: File '{input_file}' not found.")
        await browser.close()
        return

    # Create output folder if it doesn't exist
    os.makedirs(output_folder, exist_ok=True)

    # Lists to store results
    results = []

    print("Processing URLs...")

    # Visit each URL, capture screenshots, and check accessibility
    for i, url in enumerate(urls, start=1):
        print(f"Processing URL {i}/{len(urls)}: {url.strip()}")

        url = url.strip()  # Remove leading/trailing whitespaces and newlines
        
        # Prepend 'http://' if missing
        if not url.startswith('http://') and not url.startswith('https://'):
            url = 'http://' + url
        
        # Format the image name
        image_name = f"{i}_{url.replace('://', '_').replace('/', '_').replace('.', '_')}.png"
        output_file = os.path.join(output_folder, image_name)
        
        # Default status is 'Accessible'
        status = 'Accessible'

        try:
            await page.goto(url)
            await page.setViewport({'width': 1280, 'height': 800})  # Set viewport size
        except NetworkError as e:
            print(f"Error: Skipping URL '{url}' due to network error: {e}")
            status = 'Not Accessible'
        except PageError as e:
            print(f"Error: Skipping URL '{url}' due to page error: {e}")
            status = 'Name Resolution Failure'
        
        # Capture screenshot
        await page.screenshot({'path': output_file})  

        # Check if blocked by looking for common signs of blocking
        content = await page.content()
        if "captcha" in content.lower():
            status = 'Blocked (CAPTCHA)'
        elif "blocked" in content.lower():
            status = 'Blocked'

        results.append({'Number': i, 'URL': url, 'Screenshot': image_name, 'Status': status})

    await browser.close()

    print("Processing complete.")
    
    # Create a DataFrame from the results
    df = pd.DataFrame(results)

    # Save DataFrame to Excel file
    excel_file = os.path.join(output_folder, 'website_accessibility.xlsx')
    df.to_excel(excel_file, index=False)
    print(f"Results saved to {excel_file}")

if __name__ == "__main__":
    input_file = input("Enter the file path containing the list of URLs: ")
    output_folder = input("Enter the folder name to save the screenshots and Excel file: ")
    asyncio.get_event_loop().run_until_complete(take_screenshots_and_check_accessibility(input_file, output_folder))
