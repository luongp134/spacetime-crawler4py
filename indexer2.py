from collections import defaultdict
import os
import zipfile
import nltk
import re
from bs4 import BeautifulSoup, MarkupResemblesLocatorWarning
from nltk.tokenize import word_tokenize
from nltk.stem import PorterStemmer
from nltk.data import find
from nltk.corpus import stopwords
import warnings
import json
from html import unescape
import lxml

try:
    find("tokenizers/punkt")
except LookupError:
    # If not found, download
    nltk.download("punkt")

try:
    find("corpora/stopwords")
except LookupError:
    nltk.download("stopwords")

stemmer = PorterStemmer()
# stop_words = set(stopwords.words('english'))


def preprocess_text(content):
    content = unescape(content)  # Decode escaped characters
    # Remove any warnings about the content being more like a filename than markup
    warnings.filterwarnings("ignore", category=MarkupResemblesLocatorWarning)

    # Attempt to parse content as XML first, fall back to HTML if unsuccessful
    try:
        soup = BeautifulSoup(content, "xml")  # Attempt XML parsing
    except lxml.etree.XMLSyntaxError:  # If parsing as XML fails, assume it's HTML
        soup = BeautifulSoup(content, "lxml")  # Fallback to lxml parser for HTML
    # Attempt to parse content as XML first, fall back to HTML if unsuccessful

    text = soup.get_text()

    text = text.lower()  # Normalize to lowercase
    text = re.sub(r"[^a-zA-Z0-9\s]", "", text)  # Remove non-alphanumeric characters
    tokens = word_tokenize(text)
    # Assign higher weight to words in important HTML tags
    for tag in soup.find_all(["b", "strong", "h1", "h2", "h3", "title"]):
        tag_text = tag.get_text().lower()
        tag_tokens = word_tokenize(tag_text)
        for token in tag_tokens:
            if token in tokens:
                index = tokens.index(token)
                tokens[
                    index
                ] += "_important"  # Append '_important' to distinguish from regular tokens

    # Stemming and stopwords removal
    stemmed_tokens = [stemmer.stem(token) for token in tokens if token.isalnum()]

    return stemmed_tokens


def read_zip(zip_path):
    with zipfile.ZipFile(zip_path) as z:
        for filename in z.namelist():
            if filename.endswith(".json"):  # Ensure its a JSON file
                with z.open(filename) as f:
                    content = f.read()
                    # Decode JSON content
                    json_content = json.loads(content.decode("utf-8"))
                    # Use the 'content' key to get the HTML content
                    html_content = json_content.get("content", "")
                    url = json_content.get("url", "")
                    # Check if HTML content is actually present
                    if not html_content:
                        continue
                    yield filename, html_content, url


def save_inverted_index(index, filepath="inverted_index.json"):
    with open(filepath, "w") as file:
        json.dump(index, file)


def write_partial_index(partial_index, index_num):
    with open(f"partial_index_{index_num}.json", "w") as file:
        json.dump(partial_index, file)


def write_partial_docs(partial_docs, index_num):
    with open(f"partial_doc_id_{index_num}.json", "w") as file:
        json.dump(partial_docs, file)


def merge_partial_indexes(partial_indexes):
    merged_index = defaultdict(dict)
    for index_file in partial_indexes:
        with open(index_file, "r") as file:
            partial_index = json.load(file)
            for term, postings in partial_index.items():
                merged_index[term].update(postings)
    return merged_index


def create_inverted_index(zip_path):
    print("Starting to index!")
    inverted_index = {}
    doc_id = {}
    partial_doc_id = []
    partial_doc_num = 1
    id = 0
    processed_files = set()
    partial_indexes = []
    partial_index_num = 1
    for filename, content, url in read_zip(zip_path):
        processed_files.add(filename)
        tokens = preprocess_text(content)
        unique_tokens = set(tokens)
        print(f"Processing: {url}") # Debugging line, shows file
        print(f"Tokens found: {tokens[:10]}")  # Debugging line, shows first 10 tokens

        doc_id[id] = url

        for token in unique_tokens:
            if token not in inverted_index:
                inverted_index[token] = {id: tokens.count(token)}
            else:
                if url in inverted_index[token]:
                    inverted_index[token][id] += tokens.count(token)
                else:
                    inverted_index[token][id] = tokens.count(token)

        id += 1

        # Offload the inverted index to disk every 1000 documents
        if len(processed_files) % 2000 == 0:
            write_partial_index(inverted_index, partial_index_num)
            partial_indexes.append(f"partial_index_{partial_index_num}.json")
            partial_index_num += 1
            inverted_index = {}

            write_partial_docs(doc_id, partial_doc_num)
            partial_doc_id.append(f"partial_index_{partial_doc_num}.json")
            partial_doc_num += 1
            doc_id = {}

    if len(processed_files) % 2000 != 0:
        # Write the final partial index to disk
        write_partial_index(inverted_index, partial_index_num)
        partial_indexes.append(f"partial_index_{partial_index_num}.json")
        write_partial_docs(doc_id, partial_doc_num)
        partial_doc_id.append(f"partial_index_{partial_doc_num}.json")

    # Merge the partial indexes into a final index
    final_index = merge_partial_indexes(partial_indexes)
    final_doc_id = merge_partial_indexes(partial_doc_id)

    # Save the final index to disk
    save_inverted_index(final_index, "inverted_index.json")
    save_inverted_index(final_doc_id, "doc_id.json")
    index_size = os.path.getsize("inverted_index.json") / 1024
    print(f"Number of indexed documents: {len(processed_files)}")
    print(f"Number of unique words: {len(final_index)}")
    print(f"Total size of index on disk: {index_size:.2f} KB")
    return final_index


zip_path = "developer.zip"
inverted_index = create_inverted_index(zip_path)
# print(inverted_index)
