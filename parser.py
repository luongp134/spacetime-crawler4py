from bs4 import BeautifulSoup

stop_words = {'a', 'about', 'above', 'after', 'again', 'against', 'all', 'am', 'an', 'and', 'any', 'are', "aren't", 'as', 'at', 'be', 'because', 'been', 'before', 'being', 'below', 'between', 'both', 'but', 'by', "can't", 'cannot', 'could', "couldn't", 'did', "didn't", 'do', 'does', "doesn't", 'doing', "don't", 'down', 'during', 'each', 'few', 'for', 'from', 'further', 'had', "hadn't", 'has', "hasn't", 'have', "haven't", 'having', 'he', "he'd", "he'll", "he's", 'her', 'here', "here's", 'hers', 'herself', 'him', 'himself', 'his', 'how', "how's", 'i', "i'd", "i'll", "i'm", "i've", 'if', 'in', 'into', 'is', "isn't", 'it', "it's", 'its', 'itself', "let's", 'me', 'more', 'most', "mustn't", 'my', 'myself', 'no', 'nor', 'not', 'of', 'off', 'on', 'once', 'only', 'or', 'other', 'ought', 'our', 'ours', 'ourselves', 'out', 'over', 'own', 'same', "shan't", 'she', "she'd", "she'll", "she's", 'should', "shouldn't", 'so', 'some', 'such', 'than', 'that', "that's", 'the', 'their', 'theirs', 'them', 'themselves', 'then', 'there', "there's", 'these', 'they', "they'd", "they'll", "they're", "they've", 'this', 'those', 'through', 'to', 'too', 'under', 'until', 'up', 'very', 'was', "wasn't", 'we', "we'd", "we'll", "we're", "we've", 'were', "weren't", 'what', "what's", 'when', "when's", 'where', "where's", 'which', 'while', 'who', "who's", 'whom', 'why', "why's", 'with', "won't", 'would', "wouldn't", 'you', "you'd", "you'll", "you're", "you've", 'your', 'yours', 'yourself', 'yourselves', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'j', 'k', 'l', 'm', 'n', 'o', 'p', 'q', 'r', 's', 't', 'u', 'v', 'w', 'x', 'y', 'z'}

#-----------------------helper functions ---------------------
def convert_response_to_words(response_content):
    try:
        if isinstance(response_content, bytes):
            response_content = response_content.decode('utf-8', errors='ignore')

        soup = BeautifulSoup(response_content, 'html.parser')
        
        # Remove tags and extract all text within HTML
        for style_or_script in soup(['script', 'style']):
            style_or_script.extract()  # Remove these tags and their content

        text = soup.get_text(separator=' ')  # Updated to get all remaining text
        words = text.split()
        
        return words

    except Exception as e:
        print(f"Error processing response content: {e}")
        return []

def filter_words(words) -> list:
    filtered_words = [word for word in words if word.lower() not in stop_words]
    return filtered_words

def tokenize(text) -> list:
    token_list = []
    token_chars = []
    for char in text.lower():
        if char.isalnum():
            token_chars.append(char)
        elif token_chars:
            token_list.append(''.join(token_chars))
            token_chars = []
    if token_chars:
        token_list.append(''.join(token_chars))  # Add last token if any
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
    #return 50 most common words in url dictionary where key is url string and dictionary is the words in that page
    '''
    What are the 50 most common words in the entire set of pages crawled under these domains ? (Ignore English stop words, which can be found, for example, here
Links to an external site.
) Submit the list of common words ordered by frequency.

    '''
    common_words_frequency = dict()
    for url in converted_dictionary:
        filtered_words = filter_words(converted_dictionary[url])
        word_frequencies = compute_word_frequencies(filtered_words)
        for word, count in word_frequencies.items():
            if word in common_words_frequency:
                common_words_frequency[word] += count  # Add count if word exists
            else:
                common_words_frequency[word] = count  # Initialize if not
    
    sorted_common_words = sorted(common_words_frequency.items(), key=lambda item: item[1], reverse=True)
    return sorted_common_words[:50]