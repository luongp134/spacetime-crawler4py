import re
import sys
import pickle
import os
from urllib.parse import urlparse, urljoin, urldefrag
from bs4 import BeautifulSoup
import lxml
from parser import convert_response_to_words, longest_page, fifty_common_words
from utils.subdomain import *

# Initialize subdomain tracker
subdomains = subdomainTrie()

# Paths for saving progress -- The server crashed while running, and we lost all the progress we had, so now we decided to store it into a file, so if it crashes we can just continue running it
HYPERLINKS_FILE = "hyperlinks.pkl"
URL_CONTENT_FILE = "url_content_dictionary.pkl"

# Load previous data if available
if os.path.exists(HYPERLINKS_FILE):
    with open(HYPERLINKS_FILE, "rb") as f:
        hyperlinks = pickle.load(f)
else:
    hyperlinks = set()

if os.path.exists(URL_CONTENT_FILE):
    with open(URL_CONTENT_FILE, "rb") as f:
        url_content_dictionary = pickle.load(f)
else:
    url_content_dictionary = dict()

def save_progress():
    with open(HYPERLINKS_FILE, "wb") as f:
        pickle.dump(hyperlinks, f)
    with open(URL_CONTENT_FILE, "wb") as f:
        pickle.dump(url_content_dictionary, f)

def scraper(url, resp):
    links = extract_next_links(url, resp)
    validLinks = []
    for link in links:
        if is_valid(link):
            subdomains.addLink(link)
            validLinks.append(link)
            #save what we just got because 
            save_progress()
    return validLinks

def extract_next_links(url, resp):
    if resp.status not in {200, 204} or len(resp.raw_response.content) < 500:
        print("early exit out for low content count")
        return []

    try:
        soup = BeautifulSoup(resp.raw_response.content, 'lxml') #parse html
        
        for element in soup(['script', 'style', 'nav', 'footer', 'header']):
            element.decompose()

        page_text = soup.get_text()
        # if len(page_text.strip()) < 1500: #low textual information content
        #     return []
        
        # tokens = tokenize(page_text)

        # if len(set(tokens)) < 45: #low unique tokens
        #     return []

        #store content in dictionary for each url
        url_content_dictionary[resp.url] = convert_response_to_words(resp.raw_response.content)

        #URL code
        anchors = soup.find_all('a', href=True)

        currentLinksFound = set()

        for a in anchors: #find anchor tags with href
            href = a.get('href')
            if not href: #ignore empty href
                continue
            
            try:
                parsed = urlparse(href) #parse href

                if parsed.scheme and parsed.netloc: #check for scheme and netloc = fullURL
                    fullURL = href
                else:
                    fullURL = urljoin(url,href)
                    fullURL = urldefrag(fullURL).url
                if fullURL not in hyperlinks: #duplicates
                    currentLinksFound.add(fullURL)
                    hyperlinks.add(fullURL)
            except Exception:
                continue
    except Exception:
        return currentLinksFound
    return currentLinksFound

def is_valid(url):
    try:
        url_without_fragment = urldefrag(url).url
        parsed = urlparse(url_without_fragment)
        valid_domains = [
            ".ics.uci.edu",
            "cs.uci.edu",
            ".informatics.uci.edu",
            ".stat.uci.edu",
        ]

        if (
            not parsed.scheme in {"http", "https"}
            or parsed.hostname is None
            or parsed.netloc is None
            or "?" in url
            or "&" in url
        ):
            return False

        if not any(domain in parsed.hostname for domain in valid_domains):
            return False

        if (
            re.search(r"/(search|login|logout|api|admin|raw|static)/", parsed.path.lower())
            or re.search(r"/(page|p)/?\d+", parsed.path.lower())
            or re.search(r"(sessionid|sid|session)=[\w\d]{32}", parsed.query)
            or re.match(
                r".*\.(css|js|bmp|gif|jpe?g|ico|png|tiff?|mid|mp2|mp3|mp4|img"
                r"|wav|avi|mov|mpeg|ram|m4v|mkv|ogg|ogv|pdf|ps|eps|tex|ppt|pptx|doc|docx|xls|xlsx"
                r"|data|dat|exe|bz2|tar|msi|bin|7z|psd|dmg|iso|epub|dll|cnf|tgz|sha1"
                r"|thmx|mso|arff|rtf|jar|csv|rm|smil|wmv|swf|wma|zip|rar|gz)$",
                parsed.path.lower(),
            )
            or re.search(
                r"/\d{4}/\d{2}/\d{2}/|/\d{4}-\d{2}-\d{2}/|/(19|20)[0-9]{2}/|/(19|20)[0-9]{2}$|/(19|20)[0-9]{2}-[0-9]{1,2}",
                parsed.path.lower(),
            )
        ):
            return False
        return True

    except (ValueError, TypeError) as e:
        print(f"Error for URL {url}: {e}")
        return False

def get_output():
    holder = ""

    subdomainCount = subdomains.subdomainCount()

    # Question 1: Number of unique pages found
    holder += f"1. Number of unique pages found: {len(hyperlinks)}"

    result = longest_page(url_content_dictionary)
    holder += f" \n2. Longest page: {result[0]} with {result[1]} words total\n\n"

    holder += "\n3. 50 most common words in order of most frequent to least frequent are:\n"
    url_tuple = fifty_common_words(url_content_dictionary)
    frequency_list = ""
    for i in range(len(url_tuple)):
        if i == len(url_tuple) - 1:
            frequency_list = frequency_list + url_tuple[i][0] + " -> " + str(url_tuple[i][1])
        else:
            frequency_list = frequency_list + url_tuple[i][0] + " -> " + str(url_tuple[i][1]) + ", "
        
    holder += frequency_list

    holder += "\n4. The list of all subdomains are: \n"
    subdomainCount.sort(key=lambda x: x[0])

    for subdomain, count in subdomainCount:
        holder += f"{subdomain} has {count} unique subdomains\n"

    # Write holder to a text file
    with open("result.txt", "w") as file:
        file.write(holder)

    print("Result has been written to result.txt file.")
