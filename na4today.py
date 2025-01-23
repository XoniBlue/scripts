import requests
from lxml import html

# Discord webhook URL and message ID
DISCORD_WEBHOOK_URL = "https://discord.com/api/webhooks/1330623496362921994/IoJHTKvlSHTJKxh3Us1XeIyLceifRg5leHzeM2yp1XWF9Lg_9uYlLvO0b7VCxzwddDsD"
MESSAGE_ID = "1332055495598669937"  # Replace with your message ID

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
def patch_discord_message(message):
    if not message:
        print("No message to patch. Skipping.")
        return
    
    url = f"{DISCORD_WEBHOOK_URL}/messages/{MESSAGE_ID}"  # Target the specific message
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

# Main function
def main():
    # Scrape the "Just for Today" reading
    print("Scraping the 'Just for Today' reading...")
    jft_message = scrape_just_for_today()
    if jft_message:
        print("Scraped message successfully:")
        print(jft_message)
    else:
        print("Failed to scrape the 'Just for Today' reading.")
    
    # Patch the message in Discord
    print("Patching the Discord message...")
    patch_discord_message(jft_message)

if __name__ == "__main__":
    main()
