from collections import defaultdict
import re
import threading
from bs4 import BeautifulSoup
import json

stop_words = {'a', 'about', 'above', 'after', 'again', 'against', 'all', 'am', 'an', 'and', 'any', 'are', "aren't", 'as', 'at', 'be', 'because', 'been', 'before', 'being', 'below', 'between', 'both', 'but', 'by', "can't", 'cannot', 'could', "couldn't", 'did', "didn't", 'do', 'does', "doesn't", 'doing', "don't", 'down', 'during', 'each', 'few', 'for', 'from', 'further', 'had', "hadn't", 'has', "hasn't", 'have', "haven't", 'having', 'he', "he'd", "he'll", "he's", 'her', 'here', "here's", 'hers', 'herself', 'him', 'himself', 'his', 'how', "how's", 'i', "i'd", "i'll", "i'm", "i've", 'if', 'in', 'into', 'is', "isn't", 'it', "it's", 'its', 'itself', "let's", 'me', 'more', 'most', "mustn't", 'my', 'myself', 'no', 'nor', 'not', 'of', 'off', 'on', 'once', 'only', 'or', 'other', 'ought', 'our', 'ours', 'ourselves', 'out', 'over', 'own', 'same', "shan't", 'she', "she'd", "she'll", "she's", 'should', "shouldn't", 'so', 'some', 'such', 'than', 'that', "that's", 'the', 'their', 'theirs', 'them', 'themselves', 'then', 'there', "there's", 'these', 'they', "they'd", "they'll", "they're", "they've", 'this', 'those', 'through', 'to', 'too', 'under', 'until', 'up', 'very', 'was', "wasn't", 'we', "we'd", "we'll", "we're", "we've", 'were', "weren't", 'what', "what's", 'when', "when's", 'where', "where's", 'which', 'while', 'who', "who's", 'whom', 'why', "why's", 'with', "won't", 'would', "wouldn't", 'you', "you'd", "you'll", "you're", "you've", 'your', 'yours', 'yourself', 'yourselves', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'j', 'k', 'l', 'm', 'n', 'o', 'p', 'q', 'r', 's', 't', 'u', 'v', 'w', 'x', 'y', 'z'}


class InvertedIndex:
    def __init__(self):
        self.index = defaultdict(list)  # term -> list of document IDs
        self.docTermMapping = {}  # docId -> {term: frequency}
        self.docUrls = {}  # docId -> URL or file path

        #may also need to remove this part if multi threading is not allowed
        self.lock = threading.Lock() 

    def add_document(self, docId, terms, url):
        """
        Add a document to the inverted index.

        :param docId: Unique document ID.
        :param terms: List of terms in the document.
        :param url: URL or file path of the document.
        """
        termFreq = defaultdict(int)
        for term in terms:
            termFreq[term] += 1
        
        with self.lock:
            # Add the document's term frequency and URL to the mappings
            self.docTermMapping[docId] = dict(termFreq)
            self.docUrls[docId] = url  # Store the URL or file path
            
            for term in termFreq:
                self.index[term].append(docId)

    def get_documents_for_term(self, term):
        return self.index.get(term, [])

    def get_term_frequency_in_doc(self, docId, term):
        return self.docTermMapping.get(docId, {}).get(term, 0)
    
    def get_url_for_doc(self, docId):
        return self.docUrls.get(docId, "URL not found")
    
    def save_to_file(self, file_path="inverted_index.json"):
        with open(file_path, "w") as f:
            json.dump({
                "index": self.index,
                "docTermMapping": self.docTermMapping,
                "docUrls": self.docUrls
                }, f)

    def load_from_file(self, file_path):
        with open(file_path, "r") as f:
            data = json.load(f)
            self.index = defaultdict(list, data["index"])
            self.docTermMapping = data["docTermMapping"]
            self.docUrls = data["docUrls"]

class fileMapper:
    def __init__(self):
        self.fileToId = {} # file path -> document unique id
        self.idToFile = {} # document unique id -> file path

        #may need to remove, not sure if multi threading is allowed, but makes it way faster for processing
        self.lock = threading.Lock()
        self.counter = 1

    def addFile(self,filePath):
        with self.lock:
            if filePath not in self.fileToId:
                self.fileToId[filePath] = self.counter
                self.idToFile[self.counter] = filePath
                self.counter +=1
            return self.counter - 1

    def getFileById(self,id):
        return self.idToFile.get(id,None)
    
    def getFileByPath(self,filePath):
        return self.fileToId.get(filePath,None)

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