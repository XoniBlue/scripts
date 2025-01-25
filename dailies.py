import datetime
import csv
import requests
import sys
import time
from io import StringIO
import threading
from lxml import html
from colorama import init, Fore, Back, Style  # Import colorama for colored output

# Initialize colorama
init(autoreset=True)

# Constants
DISCORD_WEBHOOK_URL = "https://discord.com/api/webhooks/1330623496362921994/IoJHTKvlSHTJKxh3Us1XeIyLceifRg5leHzeM2yp1XWF9Lg_9uYlLvO0b7VCxzwddDsD"
CSV_URL = 'https://docs.google.com/spreadsheets/d/e/2PACX-1vT6bsEb4n6bdbtV08L8_X9hGiuUfsKBPiSUtoTqnQ4ImAoXB9rdTACMr6Y10j6UE2htZma0r-Kulp5Q/pub?output=csv'
MESSAGE_IDS = {
    "Reflection": "1330767987363549244",
    "Inspiration": "1330767992988106783",
    "Thought": "1330767999258464277",
    "Meditation": "1330768004597944402",
    "Prayer": "1330768011187064913",
    "JustForToday": "1332055495598669937",  # Assuming you want the Just For Today message updated too
    "CoDAReading": "1332565311748046949"  # Assuming a new field for CoDA Weekly Reading
}

# Spinner animation
spinner = ['|', '/', '-', '\\']

# Function to display the animated spinner
def animate_spinner(duration=3):
    for i in range(duration):
        sys.stdout.write(f"\r{spinner[i % len(spinner)]} Please wait...    ")
        sys.stdout.flush()
        time.sleep(0.2)
    sys.stdout.write("\r      dude                    \r")  # Clear the spinner line


# Function to scrape "Just for Today" reading
def scrape_just_for_today():
    url = "https://www.jftna.org/jft/"
    response = requests.get(url)
    if response.status_code == 200:
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
        print(Fore.GREEN + "Successfully fetched the Just For Today page!")
        return message
    else:
        print(Fore.RED + "Failed to fetch the Just For Today page.")
        return None

# Function to scrape the CoDA Weekly Reading
def scrape_coda_weekly_reading():
    url = "https://coda.org/weekly-reading/"
    response = requests.get(url)
    if response.status_code == 200:
        # Parse the page content using lxml
        tree = html.fromstring(response.content)
        
        # Helper function to safely extract text from an XPath
        def get_text_safe(xpath):
            element = tree.xpath(xpath)
            if element:
                return element[0].text_content().strip()
            else:
                return "N/A"
        
        # Extract the page title
        page_title = get_text_safe("//h1[@class='pageTitle']")
        
        # Extract the weekly reading title
        weekly_reading_title = get_text_safe("//h2[@class='entry-title']")
        
        # Extract the main content
        content_paragraphs = tree.xpath("//div[contains(@class, 'pageContent')]//p")
        content = "\n\n".join(p.text_content().strip() for p in content_paragraphs if p.text_content().strip())
                     
        # Formatting the message
        message = (
            f"`CoDA Weekly Reading`\n"
            f"# {page_title}\n\n"
            f"> ## {weekly_reading_title}\n\n"
            f"{content}\n\n"
        )
        print(Fore.GREEN + "Successfully fetched the CoDA Weekly Reading page!")
        return message
    else:
        print(Fore.RED + "Failed to fetch the CoDA Weekly Reading page.")
        return None

# Function to patch the message in Discord with simplified logging
def patch_discord_message(message, message_id, section_title):
    if not message:
        return
    
    url = f"{DISCORD_WEBHOOK_URL}/messages/{message_id}"  # Target the specific message
    payload = {
        "content": message  # Updated message content
    }
    headers = {
        "Content-Type": "application/json"
    }
    
    # Display spinner during the HTTP request
    spinner_thread = threading.Thread(target=animate_spinner, args=(5,))
    spinner_thread.start()
    
    response = requests.patch(url, json=payload, headers=headers)
    
    spinner_thread.join()  # Ensure spinner stops before printing response

    # Log the response status and content for debugging
    if response.status_code == 200:  # Success
        print(Fore.CYAN + f"Patched {section_title} successfully!")  # Colored success message
    else:
        print(Fore.RED + f"Failed to patch {section_title}. Status: {response.status_code}, Response: {response.text}")

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
        return None

# Find today's row based on the date
def get_row_for_today(csv_data, today_date):
    csv_file = StringIO(csv_data)  # Use StringIO to treat the string as a file
    reader = csv.reader(csv_file)
    
    # Skip the header row (if any)
    header = next(reader)
    
    for row in reader:
        # Clean the date by stripping unwanted characters (like '|')
        cleaned_date = row[0].strip().lstrip('|').strip()  # Remove leading/trailing spaces and '|'
        
        # Ensure cleaned date is a valid match by removing any potential extra characters
        if cleaned_date == today_date:
            print(Fore.GREEN + f"Found the correct date: {today_date}")
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
    
    # Display spinner during the HTTP request
    spinner_thread = threading.Thread(target=animate_spinner, args=(5,))
    spinner_thread.start()
    
    response = requests.patch(url, json=payload)
    
    spinner_thread.join()  # Ensure spinner stops before printing response

    # Log response status and content for debugging
    if response.status_code == 200:
        print(Fore.CYAN + f"Patched {section_title} successfully!")  # Colored success message
    else:
        print(Fore.RED + f"Failed to patch {section_title}. Status: {response.status_code}")

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
        
        # Patch JustForToday and CoDAReading sections with proper naming
        jft_message = scrape_just_for_today()
        if jft_message:
            patch_discord_message(jft_message, MESSAGE_IDS["JustForToday"], "Just For Today")

        coda_message = scrape_coda_weekly_reading()
        if coda_message:
            patch_discord_message(coda_message, MESSAGE_IDS["CoDAReading"], "CoDA Reading")

        # After successful patching of all sections
        print(Fore.GREEN + "Dailies Patched Successfully! It Works If You Work IT!")
    else:
        print(Fore.RED + "No data found for today.")

# Main function to run the app
def main():
    # Fetch the CSV data from the published Google Sheet
    csv_data = fetch_csv_data()
    
    if not csv_data:
        print(Fore.RED + "No data found.")
        return
    
    # Get today's date
    today_date = get_today_date()

    # Find today's row based on the date
    row_for_today = get_row_for_today(csv_data, today_date)

    # Send or patch all sections to Discord
    send_all_sections(row_for_today)

if __name__ == "__main__":
    main()
