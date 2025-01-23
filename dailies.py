import datetime
import csv
import requests
import sys
import time
from io import StringIO
import threading
from lxml import html

# Constants
DISCORD_WEBHOOK_URL = "https://discord.com/api/webhooks/1330623496362921994/IoJHTKvlSHTJKxh3Us1XeIyLceifRg5leHzeM2yp1XWF9Lg_9uYlLvO0b7VCxzwddDsD"
CSV_URL = 'https://docs.google.com/spreadsheets/d/e/2PACX-1vT6bsEb4n6bdbtV08L8_X9hGiuUfsKBPiSUtoTqnQ4ImAoXB9rdTACMr6Y10j6UE2htZma0r-Kulp5Q/pub?output=csv'
MESSAGE_IDS = {
    "Reflection": "1330767987363549244",
    "Inspiration": "1330767992988106783",
    "Thought": "1330767999258464277",
    "Meditation": "1330768004597944402",
    "Prayer": "1330768011187064913",
    "JustForToday": "1332055495598669937"  # Assuming you want the Just For Today message updated too
}

# Function to scrape "Just for Today" reading
def scrape_just_for_today():
    url = "https://www.jftna.org/jft/"
    response = requests.get(url)
    if response.status_code == 200:
        print("Page fetched successfully!")
        
        # Parse the page content using lxml
        tree = html.fromstring(response.content)
        
        # Helper function to safely extract text from an XPath
        def get_text_safe(xpath):
            element = tree.xpath(xpath)
            if element:
                return element[0].text_content().strip()
            else:
                return "N/A"
        
        # Extract data using the correct XPath for each element
        date = get_text_safe("//h2")  # Date is inside <h2>
        title = get_text_safe("//h1")  # Title is inside <h1>
        page_number = get_text_safe("//td[contains(text(),'Page')]")  # Page number
        quote = get_text_safe("//i")  # The quote is inside <i>
        
        # Use the XPath you provided for "Basic Text" page number
        basic_text_page_number = get_text_safe("//tr[5]")
        basic_text_passage = get_text_safe("//tr[6]")
        
        # Extract the Just for Today Passage (looking for the <b> Just for Today: text)
        passage = get_text_safe("//tr[7]")
        
        # Formatting the message
        message = (
            f"`Just for Today N.A.`\n"
            f"-# {date}\n"
            f"# {title}\n"
            f"-# {page_number}\n\n"
            f"_{quote}_\n\n"
            f"**{basic_text_page_number}**:\n\n"
            f"**{basic_text_passage}**:\n\n"
            f"_**{passage}**_"
        )
        return message
    else:
        print(f"Failed to fetch the page. Status code: {response.status_code}")
    return None

# Function to patch the message in Discord
def patch_discord_message(message, message_id):
    if not message:
        print("No message to patch. Skipping.")
        return
    
    url = f"{DISCORD_WEBHOOK_URL}/messages/{message_id}"  # Target the specific message
    payload = {
        "content": message  # Updated message content
    }
    headers = {
        "Content-Type": "application/json"
    }
    response = requests.patch(url, json=payload, headers=headers)
    if response.status_code == 200:  # Success
        print("Message successfully patched in Discord.")
    else:
        print(f"Failed to patch message. Status code: {response.status_code}, Response: {response.text}")

# Get today's date in 'MMMM dd' format (e.g., January 19)
def get_today_date():
    return datetime.datetime.now().strftime('%B %d')  # 'January 19'

# Fetch the CSV data from the URL
def fetch_csv_data():
    response = requests.get(CSV_URL)
    if response.status_code == 200:
        response.encoding = 'utf-8'  # Set encoding to UTF-8
        return response.text  # Return the CSV content as a string
    else:
        print(f"Failed to fetch data. HTTP Status Code: {response.status_code}")
        return None

# Find today's row based on the date
def get_row_for_today(csv_data, today_date):
    csv_file = StringIO(csv_data)  # Use StringIO to treat the string as a file
    reader = csv.reader(csv_file)
    
    # Skip the header row (if any)
    header = next(reader)
    
    print(f"Looking for date: {today_date}", end="")  # Debugging: print today's date
    
    for row in reader:
        # Clean the date by stripping unwanted characters (like '|')
        cleaned_date = row[0].strip().lstrip('|').strip()  # Remove leading/trailing spaces and '|'
        
        print(f"\rChecking row: {cleaned_date}", end="")  # Update the same line with each row check
        
        # Ensure cleaned date is a valid match by removing any potential extra characters
        if cleaned_date == today_date:
            print(f"\rCurrent Date Found: {today_date}")  # Update line once the date is found
            return row
    return None  # If no data found for today's date

# Function to send or patch each section to Discord (PATCH instead of POST)
def send_or_patch_to_discord(section_title, section_text, message_id, date):
    # Format: Title with backticks, date with `-#`, and the section content
    content = f"**`{section_title}`:**\n-# {date}\n{section_text}"
    
    payload = {
        'content': content
    }

    url = f"{DISCORD_WEBHOOK_URL}/messages/{message_id}"
    response = requests.patch(url, json=payload)
    
    # Log response status and content for debugging
    if response.status_code == 200:
        print(f"Patched {section_title} successfully!")
    else:
        print(f"Failed to patch {section_title}. Status: {response.status_code}")

# Function to format and send all sections
def send_all_sections(row):
    if row:
        today_date = get_today_date()  # Get today's date once to prepend
        
        # Reflection: Format as italics using markdown
        send_or_patch_to_discord("Reflection", f">>> {row[1].strip()}", message_id=MESSAGE_IDS["Reflection"], date=today_date)

        # Inspiration: Format as a markdown blockquote
        send_or_patch_to_discord("Inspiration", f"> _**{row[2]}**_", message_id=MESSAGE_IDS["Inspiration"], date=today_date)
        
        # Thought: Format as markdown blockquote
        send_or_patch_to_discord("Thought", f">>> {row[3].strip()}", message_id=MESSAGE_IDS["Thought"], date=today_date)
        
        # Meditation: Format as markdown blockquote
        send_or_patch_to_discord("Meditation", f">>> *{row[4].strip()}*", message_id=MESSAGE_IDS["Meditation"], date=today_date)
        
        # Prayer: Check if row has enough columns to avoid IndexError
        if len(row) > 5 and row[5].strip():  # Added strip to check for empty Prayer section
            send_or_patch_to_discord("Prayer", f">>> _**{row[5].strip()}**_", message_id=MESSAGE_IDS["Prayer"], date=today_date)
        else:
            print("Prayer section is missing or empty in today's row.")
        
        # After successful patching of all sections
        print("Dailies Patched Successfully! It Works If You Work IT!")
    else:
        print("No data found for today.")

# Main function to run the app
def main():
    # Fetch the CSV data from the published Google Sheet
    csv_data = fetch_csv_data()
    
    if not csv_data:
        print("No data found.")
        return
    
    # Get today's date
    today_date = get_today_date()

    # Find today's row based on the date
    row_for_today = get_row_for_today(csv_data, today_date)

    # Send or patch all sections to Discord
    send_all_sections(row_for_today)

    # Scrape the "Just for Today" reading
    print("Scraping the 'Just for Today' reading...")
    jft_message = scrape_just_for_today()
    if jft_message:
        print("Scraped message successfully:")
        print(jft_message)
    else:
        print("Failed to scrape the 'Just for Today' reading.")
    
    # Patch the message in Discord for Just For Today
    patch_discord_message(jft_message, MESSAGE_IDS["JustForToday"])

if __name__ == "__main__":
    main()
