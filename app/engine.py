import random
import config
from bs4 import BeautifulSoup
from dotenv import load_dotenv
import requests
import time
import pyshorteners

def configure():
    """Protected info configuration"""
    load_dotenv()

def confirmation_email(link):
    something = "something"
    confirm_email = random.choice(config.EMAIL_CONFIRMATIONS)
    return f"{confirm_email}\n P.S: Here is a link to confirm your email.\n {link}"

def extract_quotes_with_writers(filename, clippings_path):
    """Takes My Clippings.txt and extracts it to a formatted string"""
    with open(rf"{clippings_path}/{filename}", "r", encoding="utf-8") as text_file:
        text = text_file.read()
        lines = text.splitlines()
        # Initialize an empty list to store the quotes and writers
        quotes_with_writers = []
        # Loop through the lines and extract the quotes and writers
        for line in lines:
            # Check if the line starts with a quotation mark
            if line.startswith('“') or line.startswith("- Your"):
                lines.remove(line)
            else:
                quotes_with_writers.append(line)
            quotes_formatted = []
            [quotes_formatted.append(x) for x in quotes_with_writers if x != '==========']
            if len(quotes_formatted) % 2 == 0:
                pair_list = [[quotes_formatted[i], quotes_formatted[i + 1]] for i in range(0, len(quotes_formatted), 2)]
            else:
                pair_list = [[quotes_formatted[i], quotes_formatted[i + 1]] for i in
                             range(0, len(quotes_formatted) - 1, 2)]
        return pair_list


def get_random_quote():
    """Scrapes the random quote of the internet when sometimes one of them does not work."""
    the_request = requests.get(url="https://www.litquotes.com/random-words-of-wisdom.php").content
    soup = BeautifulSoup(the_request, 'html.parser')
    find_quote = soup.find('span')
    print(find_quote.text)
    return find_quote.text


def also_get_random_quote():
    """Scrapes the random quote of the internet."""
    response = requests.get('https://api.quotable.io/random')
    r = response.json()
    quote = f"{r['content']}, {r['author']}"
    print(quote)
    return quote




class UniqueIDGenerator:
    def __init__(self):
        self.counter = 0

    def generate_id(self):
        current_time = int(time.time() * 1000)
        unique_id = int(str(current_time) + str(self.counter))
        self.counter += 1
        return unique_id

def link_shortener(url):
    obj = pyshorteners.Shortener()
    link = obj.tinyurl.short(url)
    return link


def generate_custom_id():
    unique_id = UniqueIDGenerator()
    real_id = unique_id.generate_id()
    return real_id



