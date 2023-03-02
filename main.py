import random
import requests
from bs4 import BeautifulSoup
import itertools

#-----------------------------------------------------------ENGINE------------------------------------------------------
def get_random_quote_from_kindle():
    check_letter = '-'
    with open('documents/My Clippings.txt','r',encoding='utf-8') as quotes:
        kindle_quotes = quotes.readlines()
        quote_list = [idx for idx in kindle_quotes if idx[0] != check_letter and idx[0] != '=']
        formatted_quotes = []
        for i in range(len(quote_list)):
            if quote_list[i].startswith('\n'):
                continue
            if quote_list[i].endswith('\n'):
                quote = quote_list[i].strip()
                author = quote_list[i - 1].strip()
                formatted_quote = f"{author}: {quote}"
                formatted_quotes.append(formatted_quote)
        random_kindle_quote = random.choice(formatted_quotes)
        print(random_kindle_quote)
        return random_kindle_quote
def get_random_quote():
    request = requests.get(url="https://www.litquotes.com/random-words-of-wisdom.php").content
    soup = BeautifulSoup(request, 'html.parser')
    find_quote = soup.find('span')
    print(find_quote.text)
    return find_quote

def also_get_random_quote():
        response = requests.get('https://api.quotable.io/random')
        r = response.json()
        quote = f"{r['content']}, {r['author']}"
        print(quote)
        return quote
get_random_quote_from_kindle()
also_get_random_quote()
#-----------------------------------------------------------FLASK APP---------------------------------------------------
