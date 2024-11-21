from parser import convert_response_to_words, compute_word_frequencies
from nltk.stem import PorterStemmer
from bs4 import BeautifulSoup
import lxml
import nltk
import json
import os
from helpers.indexerHelper import *
# from indexHelper3 import *
from concurrent.futures import ThreadPoolExecutor, as_completed
import shelve
print(shelve.__file__)
import dbm.dumb as dbm
from shelve_parser import parse_shelve_files

stemmer = PorterStemmer()

#print(nltk.__version__)

def convert_freq_stemming(response_content):
    try:
        # Get stemmed tokens directly from convert_response_to_words
        stemmed_tokens = convert_response_to_words(response_content)
        frequency = compute_word_frequencies(stemmed_tokens)
    except Exception as e:
        print(f"Error processing stemmed token frequency: {e}")
        return {}
    return frequency
    pass

def json_parse(filepath):
    try:
        with open(filepath, "r+", encoding='utf-8') as file:
            file_data = json.load(file)
    except json.JSONDecodeError:
        return ""
    
    url = file_data.get("url", "No URL found")
    
    content = BeautifulSoup(file_data["content"], "lxml")
    for element in content(["script", "style"]):
        element.decompose()

    for anchor in content.find_all('a', href=True):
        anchor.decompose()

    text = ' '.join(content.get_text(separator=' ').split())

    tagDict = {
        #high importance
    "h1": [tag.get_text(strip=True) for tag in content.find_all("h1")],
    "title": [tag.get_text(strip=True) for tag in content.find_all("title")],

        #middle importance
    "h2": [tag.get_text(strip=True) for tag in content.find_all("h2")],
    "h3": [tag.get_text(strip=True) for tag in content.find_all("h3")],
    "b": [tag.get_text(strip=True) for tag in content.find_all("b")],
    "strong": [tag.get_text(strip=True) for tag in content.find_all("strong")],
    "em": [tag.get_text(strip=True) for tag in content.find_all("em")],
    "i": [tag.get_text(strip=True) for tag in content.find_all("i")],

        #low importance
    "h4": [tag.get_text(strip=True) for tag in content.find_all("h4")],
    "h5": [tag.get_text(strip=True) for tag in content.find_all("h5")],
    "h6": [tag.get_text(strip=True) for tag in content.find_all("h6")],
    "a": [tag.get_text(strip=True) for tag in content.find_all("a")],
    "p": [tag.get_text(strip=True) for tag in content.find_all("p")],
    "span": [tag.get_text(strip=True) for tag in content.find_all("span")]
    }

    return {"text": text, "tagDict": tagDict, "url": url} #string > list to stem > token > freq.

def index_document(file_path, inverted_index, file_mapper):
    thread_id = threading.get_ident()
    thread_name = threading.current_thread().name
    shelve_filename = f"shelve/thread_data_{thread_id}.db"

    print(f"[{thread_name}] Processing file: {file_path}")

    # Get the important information from the file. The text and the tagDict that will be used later
    parsed_data = json_parse(file_path)

    if parsed_data == "":
        print(f"[{thread_name}] No content found in {file_path}")
        return None

    text = parsed_data["text"]
    tagDict = parsed_data["tagDict"]
    url = parsed_data["url"]

    word_scores = calculateWordScores(text, tagDict)

    wordFreq = convert_freq_stemming(text)

    doc_id = file_mapper.addFile(file_path)

    try:
        with shelve.open(shelve_filename, flag='c', writeback=True) as shelve_db:
            shelve_db[str(doc_id)] = {
                "file_path": file_path,
                "word_scores": word_scores,
                "wordFreq": wordFreq,
                "url": url
            }
    except dbm.error as e:
        print(f"Error processing file {file_path}: {e}")
        return None

    # Get the first 5 words from the wordFreq keys
    first_five_words = list(wordFreq.keys())[:5]

    # Before adding to the inverted index, print out the document being added with the first 5 words
    print(f"[{thread_name}] Adding document {doc_id} to inverted index with words: {first_five_words}, URL: {url}")

    inverted_index.add_document(doc_id, list(wordFreq.keys()), url)

def run(indexer, file_mapper, document_paths, max_threads=10):
    inverted_index = InvertedIndex()

    with ThreadPoolExecutor(max_threads) as executor:
        # Create a "task" with the file. Each file will be handled 
        fileTask = {executor.submit(index_document, file_path, inverted_index, file_mapper): file_path for file_path in document_paths}

        for future in as_completed(fileTask):
            file_path = fileTask[future]
            #wait for the task to finish. This is to ensure the thread doesn't start processing another file until it has finished with the file it is already on
            try:
                future.result()
            except Exception as e:
                print(f"Error processing file {file_path}: {e}")

    return inverted_index

def main():
    # This path will change based on who it is. In your own local you have to change this
    main_path = "C:/Users/Mai Luong/Documents/GitHub/search_enginepy"
    document_folder = "C:/Users/Mai Luong/Documents/GitHub/search_enginepy/developer"

    # go recursively and get all the files in the subdirectory
    document_paths = []
    for root, dirs, files in os.walk(document_folder):
            for file in files:
                if file.endswith('.json'):
                    document_paths.append(os.path.join(root, file))

    file_mapper = fileMapper()
    inverted_index = InvertedIndex()

    # Start the indexing process
    inverted_index = run(inverted_index, file_mapper, document_paths)
    parse_shelve_files(main_path+"/shelves/",main_path+"/output/")
    
    # Save the inverted index to a file
    inverted_index_file = os.path.join(main_path, "inverted_index.json")
    inverted_index.save_to_file(inverted_index_file)

    print(f"Inverted index saved to {inverted_index_file}")

if __name__ == "__main__":
    main()