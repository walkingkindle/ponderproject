import random
import config
from bs4 import BeautifulSoup
from dotenv import load_dotenv
import requests
import time
import pyshorteners
import re
import string



def configure():
    """Protected info configuration"""
    load_dotenv()

def confirmation_email(link):
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



def get_writer_only(full_title):
    pattern = r'\((.*?)\)'  # Pattern to match text within parentheses
    matches = re.findall(pattern, full_title)  # Find all matches within parentheses
    if len(matches) >= 1:
        writer_name = matches[-1]  # Last match is the writer name
        if len(matches) >= 2:
            year = matches[-2]  # Second-to-last match is the year
            return f"{writer_name}, {year}"
        else:
            return writer_name
    else:
        return None

def format_kindle_clippings(clippings_path,filename):
    with open(rf"{clippings_path}/{filename}", "r", encoding="utf-8") as file:
        content = file.read()

    highlights = content.split('==========')
    highlight_list = []

    for highlight in highlights:
        highlight = highlight.strip()
        if highlight:
            highlight_list.append(highlight)

    highlight_list.sort()

    return highlight_list





def get_all_writers(clippings_path,filename):
    with open(rf"{clippings_path}/{filename}", "r", encoding="utf-8") as text_file:
        text = text_file.read()
        lines = text.splitlines()
        matches = [line for line in lines if re.match(r'^.*\([^()]+\)$', line)]
        unique_matches = list(set(matches))
        return unique_matches


def get_random_quote():
    """Scrapes the random quote of the internet when sometimes one of them does not work."""
    the_request = requests.get(url="https://www.litquotes.com/random-words-of-wisdom.php").content
    soup = BeautifulSoup(the_request, 'html.parser')
    find_quote = soup.find('span')
    writer = soup.find('a', href=lambda href: href and href.startswith('/quote_author_resp.php?AName='))
    content = [find_quote.text,writer.text]
    return content


def format_string(input_string):
    cleaned_string = input_string.strip('()')
    tuple_string = tuple(cleaned_string.split(','))

    if len(tuple_string) < 2:
        return input_string  # Return the original string if it doesn't have the expected format

    book_title = tuple_string[0].strip("'")
    author = tuple_string[1].strip("'")
    formatted_string = f"{book_title} - {author}"
    return formatted_string


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



