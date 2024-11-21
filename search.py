from collections import defaultdict
import math
from nltk.stem import PorterStemmer
from nltk.corpus import stopwords
import re
from urllib.parse import urlparse
import time
from parser import tokenize
import shelve
import os

# this should preprocess what user entered, and change it into appropriate suffix (token)
def preprocess_input(inputs):
    stemmer = PorterStemmer()
    stopword = set(stopwords.words('english'))
    lowered_i = inputs.lower()
    valid_i = re.sub(r'[^a-zA-Z0-9\s]', '', lowered_i)  # check if non letter/int word is present
    # REMINDER: change this to our tokenizer at M3
    tokens = tokenize(valid_i)
    # isalnum recheck if the word is valid (no non-letter/int character)
    stem = [stemmer.stem(v) for v in tokens if v.isalnum() and v not in stopword]
    return stem

# this should be the main program for searching.
def AND_search(inputs, inverted_index):
    tokens = preprocess_input(inputs)
    if tokens and tokens[0] in inverted_index:
        # Start with the set of documents for the first token
        documents = set(inverted_index[tokens[0]].keys())
    else:
        return []  # No documents found for the first token

    # Perform AND operation across all tokens
    for token in tokens[1:]:
        if token in inverted_index:
            documents &= set(inverted_index[token].keys())
        else:
            return []  # If a token isn't found, no matches for AND

    # Get URLs for the resulting documents
    urls = []
    for doc_id in documents:
        urls.append(doc_id)  # Assuming `doc_id` is the URL in this structure

    return urls


def OR_search(inputs, inverted_index):
    tokens = preprocess_input(inputs)
    documents = set()

    # Collect all documents containing any of the tokens
    for token in tokens:
        if token in inverted_index:
            documents.update(inverted_index[token].keys())

    if not documents:
        return []

    # Get URLs for the resulting documents
    urls = []
    for doc_id in documents:
        urls.append(doc_id)  # Assuming `doc_id` is the URL in this structure

    return urls


def cmd_search():
    while True:
        user_input = input("Enter your inputs (Q to quit): ")

        if user_input.lower() != "q":
            start_time = time.time()
            result = AND_search(user_input, inverted_index)
            search_time = (time.time() - start_time) * 1000
            print(f"This search took {search_time:.2f} ms")

            if len(result) == 0:
                print("No results found!!! Performing less strict 'OR-search'.")
                start_time = time.time()
                result = OR_search(user_input, inverted_index)
                search_time = (time.time() - start_time) * 1000
                print(f"Additional OR search took {search_time:.2f} ms")
                if len(result) == 0:
                    print("Still no results found!!!")
                    continue

            print(f"Top 10 search results for {user_input}:")
            count = 0
            visited_urls = set()
            for url in result:
                parsed_url = urlparse(url)
                # Normalize the URL by removing file extensions
                path_without_extension = re.sub(r'\.\w+$', '', parsed_url.path)

                if path_without_extension not in visited_urls:
                    print(url)
                    visited_urls.add(path_without_extension)
                    count += 1
                if count >= 10:  # Limit to top 10 unique URLs
                    break
        else:
            break
            
if __name__ == "__main__":
    cmd_search()