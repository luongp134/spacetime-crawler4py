from bs4 import BeautifulSoup
import nltk
from nltk.corpus import stopwords

nltk.download('stopwords', quiet=True)

#-----------------------helper functions ---------------------
def convert_response_to_words(response_content):
    try:
        if isinstance(response_content, bytes):
            response_content = response_content.decode('utf-8', errors='ignore')

        soup = BeautifulSoup(response_content, 'html.parser')
        
        # Remove tags and extract all text within HTML
        for style_or_script in soup(['script', 'style']):
            style_or_script.extract()  # Remove these tags and their content

        text = soup.get_text(separator=' ')
        words = tokenize(text)  # Use tokenize function to get alphanumeric words only
        
        return words

    except Exception as e:
        print(f"Error processing response content: {e}")
        return []

def filter_words(words) -> list:
    try:
        sw = set(stopwords.words('english'))  # Use set for faster lookups
        filtered_words = [word for word in words if word.lower() not in sw]
        return filtered_words
    except Exception as e:
        print(f"Error filtering words: {e}")
        return []


def tokenize(text) -> list:
    token_list = []
    token_chars = []
    for char in text.lower():
        if char.isalnum():
            token_chars.append(char)
        elif token_chars:
            token = ''.join(token_chars)
            if any(c.isalpha() for c in token):  # Ensure token has letters
                token_list.append(token)
            token_chars = []
    if token_chars:
        token = ''.join(token_chars)
        if any(c.isalpha() for c in token):  # Ensure token has letters
            token_list.append(token)
    return token_list

def compute_word_frequencies(token_list: list) -> dict:
    frequencies = {}
    for token in token_list:
        frequencies[token] = frequencies.get(token, 0) + 1
    return frequencies

def print_frequencies(frequencies: dict) -> None:
    order = sorted(frequencies.items(), key=lambda item: item[1], reverse=True)
    for token, freq in order:
        print(f"{token} -> {freq}")

def common_tokens(function, text1, text2):
    text1_tokens = function(text1)
    if not text1_tokens:
        return False
    text2_tokens = function(text2)
    if not text2_tokens:
        return False
    
    text1_frequencies = compute_word_frequencies(text1_tokens)
    text2_frequencies = compute_word_frequencies(text2_tokens)

    text1_tokens_dup_removed = set(text1_frequencies.keys())
    text2_tokens_dup_removed = set(text2_frequencies.keys())

    common_tokens = text1_tokens_dup_removed & text2_tokens_dup_removed

    return common_tokens
#-----------------------------------------------------------------------------

#functions to use for scraper.py
def convert_response_to_text_dictionary(url_dictionary):
    for url in url_dictionary:
        words = convert_response_to_words(url_dictionary[url])
        url_dictionary[url] = words

def longest_page(converted_dictionary) -> tuple:
    longest_length = 0
    longest_page = ""
    
    for url in converted_dictionary:
        word_length = len(converted_dictionary[url])
        if word_length >= longest_length:
            longest_length = word_length
            longest_page = url
    
    return (longest_page, longest_length)

def fifty_common_words(converted_dictionary) -> list:
    common_words_frequency = {}
    for url in converted_dictionary:
        filtered_words = filter_words(converted_dictionary[url])
        
        # Filter out words that are less than 2 letters long
        filtered_words = [word for word in filtered_words if len(word) >= 3]
        
        word_frequencies = compute_word_frequencies(filtered_words)
        for word, count in word_frequencies.items():
            if word in common_words_frequency:
                common_words_frequency[word] += count  # Add count if word exists
            else:
                common_words_frequency[word] = count  # Initialize if not
    
    sorted_common_words = sorted(common_words_frequency.items(), key=lambda item: item[1], reverse=True)
    return sorted_common_words[:50]