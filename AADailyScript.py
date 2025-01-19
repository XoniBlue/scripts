import datetime
import csv
import requests
import sys
import time
from io import StringIO
import threading

# URL of the published CSV file (your provided URL)
CSV_URL = 'https://docs.google.com/spreadsheets/d/e/2PACX-1vT6bsEb4n6bdbtV08L8_X9hGiuUfsKBPiSUtoTqnQ4ImAoXB9rdTACMr6Y10j6UE2htZma0r-Kulp5Q/pub?output=csv'

# Your Discord webhook URL (using the provided URL)
DISCORD_WEBHOOK_URL = 'https://discord.com/api/webhooks/1330623496362921994/IoJHTKvlSHTJKxh3Us1XeIyLceifRg5leHzeM2yp1XWF9Lg_9uYlLvO0b7VCxzwddDsD'

# Provided message IDs
MESSAGE_IDS = {
    "Reflection": "1330664479784173601",
    "Inspiration": "1330664485014212730",
    "Thought": "1330664485739823138",
    "Meditation": "1330664487681916928",
    "Prayer": "1330664488747401271"
}

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

# Function to display the spinning cursor
def spin_cursor():
    global done
    while not done:
        for cursor in '|/-\\':
            sys.stdout.write(f'\r{cursor} Working...')  # Overwrites the previous character
            sys.stdout.flush()  # Ensure the cursor spins
            time.sleep(0.1)

# Function to display progress message
def show_progress(message, sleep_time=1):
    sys.stdout.write(f'\r{message}...')  # Overwrites the previous message
    sys.stdout.flush()  # Ensure the message is updated
    time.sleep(sleep_time)

# Function to send or update each section to Discord (PATCH instead of POST)
def send_or_patch_to_discord(section_title, section_text, message_id, date):
    global done
    
    # Start spinning cursor thread
    done = False
    spinner_thread = threading.Thread(target=spin_cursor)
    spinner_thread.start()
    
    # Format: Title with backticks, date with `-#`, and the section content
    content = f"**`{section_title}`:**\n-# {date}\n{section_text}"
    
    payload = {
        'content': content
    }

    url = f"{DISCORD_WEBHOOK_URL}/messages/{message_id}"
    response = requests.patch(url, json=payload)
    
    # Stop the spinning cursor
    done = True
    spinner_thread.join()
    
    # Log response status and content for debugging
    if response.status_code == 200:
        show_progress(f"Patched {section_title} successfully!")
    else:
        show_progress(f"Failed to patch {section_title}. Status: {response.status_code}")

# Function to format and send all sections
def send_all_sections(row):
    if row:
        today_date = get_today_date()  # Get today's date once to prepend
        
        # Reflection: Format as italics using markdown
        send_or_patch_to_discord("Reflection motherfucker", f">>> {row[1].strip()}", message_id=MESSAGE_IDS["Reflection"], date=today_date)

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
            show_progress("Prayer section is missing or empty in today's row.", sleep_time=0.5)
        
        # After successful patching of all sections
        show_progress("Dailies Patched Successfully! It Works If You Work IT!", sleep_time=1)
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

if __name__ == '__main__':
    main()
