import json
import os
import threading
import re
from collections import defaultdict
import zipfile
from bs4 import BeautifulSoup
from html import unescape
from nltk.tokenize import word_tokenize
from nltk.stem import PorterStemmer

# Assuming stemming is done using SnowballStemmer for this example
stemmer = PorterStemmer()


class InvertedIndex:
    def __init__(self):
        self.index = defaultdict(list)  # term -> list of document IDs
        self.docTermMapping = {}  # docId -> {term: frequency}
        self.lock = threading.Lock()  # optional for multi-threading scenarios

    def add_document(self, docId, terms):
        termFreq = defaultdict(int)
        for term in terms:
            termFreq[term] += 1

        with self.lock:
            self.docTermMapping[docId] = dict(termFreq)

            for term in termFreq:
                self.index[term].append(docId)

    def get_documents_for_term(self, term):
        return self.index.get(term, [])

    def get_term_frequency_in_doc(self, docId, term):
        return self.docTermMapping.get(docId, {}).get(term, 0)

    def save_to_file(self, file_path="inverted_index.json"):
        with open(file_path, "w") as f:
            json.dump({"index": self.index, "docTermMapping": self.docTermMapping}, f)

    def load_from_file(self, file_path):
        with open(file_path, "r") as f:
            data = json.load(f)
            self.index = defaultdict(list, data["index"])
            self.docTermMapping = data["docTermMapping"]


class FileMapper:
    def __init__(self):
        self.fileToId = {}  # file path -> document unique id
        self.idToFile = {}  # document unique id -> file path
        self.lock = threading.Lock()
        self.counter = 1

    def add_file(self, filePath):
        with self.lock:
            if filePath not in self.fileToId:
                self.fileToId[filePath] = self.counter
                self.idToFile[self.counter] = filePath
                self.counter += 1
            return self.counter - 1

    def get_file_by_id(self, id):
        return self.idToFile.get(id, None)

    def get_file_by_path(self, filePath):
        return self.fileToId.get(filePath, None)

def calculateWordScores(text, tagDict):

    #These are just made up, i guess we'll probably have to test and see which ones work best
    importanceScores = {
        "high": 8,
        "middle": 4,
        "low": 2.5,
        "text": 0.75
    }
    
    wordScores = defaultdict(float)
    
    for tag_type, tags in tagDict.items():
        if tag_type in ["h1", "title"]:
            importance = "high"
        elif tag_type in ["h2", "h3", "b", "strong", "em", "i"]:
            importance = "middle"
        elif tag_type in ["h4", "h5", "h6", "a", "p", "span"]:
            importance = "low"
        else:
            continue
        

    #count the score for the words that are in tags
    for tagText in tags:
        for word in tagText:
            wordScores[word] += importanceScores[importance]
    
    #count the score for the words that are just in the content
    for word in text:
        wordScores[word] += importanceScores["text"]
    
    return dict(wordScores)

def convert_response_to_words(response_content):
    content = unescape(response_content)  # Decode escaped characters
    # Remove any warnings about the content being more like a filename than markup
    # Attempt to parse content as XML first, fall back to HTML if unsuccessful
    try:
        soup = BeautifulSoup(response_content, "xml")  # Attempt XML parsing
    except:
        soup = BeautifulSoup(response_content, "lxml")  # Fallback to lxml parser for HTML

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

    # Stemming
    stemmed_tokens = [stemmer.stem(token) for token in tokens if token.isalnum()]
    return stemmed_tokens

class Indexer:
    def __init__(self):
        self.inverted_index = InvertedIndex()
        self.file_mapper = FileMapper()
        self.partial_indexes = []
        self.partial_doc_id = []
        self.processed_files = set()

    def create_inverted_index(self, document_folder):
        print("Starting to index!")
        id = 0
        partial_index_num = 1
        partial_doc_num = 1
        processed_files = set()

        # Iterate through zip files (assuming a read_zip method exists)
        for root, _, files in os.walk(document_folder):
            for filename in files:
                if filename.endswith('.json'):
                    file_path = os.path.join(root, filename)
                    processed_files.add(file_path)

                    # Read the file content
                    with open(file_path, 'r', encoding='utf-8') as file:
                        content = file.read()

                    # Tokenize the content
                    tokens = convert_response_to_words(content)

                    print(f"Processing: {file_path}")
                    print(f"Tokens found: {tokens[:10]}")

                    # Add the file to the file mapper and get a document ID
                    doc_id = self.file_mapper.add_file(file_path)

                    # Add document to the inverted index
                    self.inverted_index.add_document(doc_id, tokens)

                    # Offload the inverted index to disk every 2000 documents
                    if len(processed_files) % 2000 == 0:
                        self.write_partial_index(partial_index_num)
                        partial_index_num += 1

                        self.write_partial_docs(partial_doc_num)
                        partial_doc_num += 1

        # Merge the partial indexes into a final index
        self.merge_partial_indexes()

        # Save final index
        self.inverted_index.save_to_file("inverted_index.json")
        print(f"Number of indexed documents: {len(processed_files)}")
        return self.inverted_index

    def write_partial_index(self, partial_index_num):
        partial_index = {
            "index": self.inverted_index.index,
            "docTermMapping": self.inverted_index.docTermMapping,
        }
        with open(f"partial_index_{partial_index_num}.json", "w") as file:
            json.dump(partial_index, file)

    def write_partial_docs(self, partial_doc_num):
        with open(f"partial_doc_id_{partial_doc_num}.json", "w") as file:
            json.dump(self.file_mapper.fileToId, file)

    def merge_partial_indexes(self):
        merged_index = defaultdict(dict)
        for partial_index_file in self.partial_indexes:
            with open(partial_index_file, "r") as file:
                partial_index = json.load(file)
                for term, postings in partial_index["index"].items():
                    if term not in merged_index:
                        merged_index[term] = postings
                    else:
                        merged_index[term].update(postings)
        self.inverted_index.index = merged_index