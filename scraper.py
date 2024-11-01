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
url_content_dictionary = {}
crawled_count = 0
uniqueURL = set()


def scraper(url, resp):
    global crawled_count
    links = extract_next_links(url, resp)
    validLinks = []
    for link in links:
        if is_valid(link):
            subdomains.addLink(link)
            validLinks.append(link)
            crawled_count += 1 
            
            # Call save_progress after each valid link is processed
            #save_progress()
            if crawled_count % 1000 == 0:
                get_output()
    return validLinks

def extract_next_links(url, resp):
    if resp.status not in {200, 601, 602, 608}:
        print("Early exit out due to invalid URL status.")
        return [] 
    if len(resp.raw_response.content) < 500:
        print("Early exit out due to low information value")
        return []
    if len(convert_response_to_words(resp.raw_response.content)) <= 100:
        print("Early exit out due to low information content")
        return []

    currentLinksFound = set()  # Ensure this is initialized
    global uniqueURL

    try:
        soup = BeautifulSoup(resp.raw_response.content, 'lxml')  # Parse HTML

        for element in soup(['script', 'style', 'nav', 'footer', 'header']):
            element.decompose()
        
        # Store content in dictionary for each URL
        url_content_dictionary[resp.url] = convert_response_to_words(resp.raw_response.content)

        # URL code
        anchors = soup.find_all('a', href=True)
        for a in anchors:  # Find anchor tags with href
            href = a.get('href')
            if not href:  # Ignore empty href
                continue

            try:
                parsed = urlparse(href)  # Parse href

                if parsed.scheme and parsed.netloc:  # Check for scheme and netloc = fullURL
                    fullURL = href
                else:
                    fullURL = urljoin(url, href)
                    
                    clean_url = urldefrag(fullURL).url
                    fragment = urldefrag(fullURL).fragment

                    uniqueURL.add(clean_url)
                if fullURL not in currentLinksFound:  # Duplicates
                    currentLinksFound.add(fullURL)
            except Exception:
                continue
    except Exception as e:
        print(f"Exception occurred: {e}")

    return currentLinksFound

def is_valid(url):
    try:
        #url_without_fragment = urldefrag(url).url
        parsed = urlparse(url)#_without_fragment)
        valid_domains = [
            ".ics.uci.edu",
            "cs.uci.edu",
            ".informatics.uci.edu",
            ".stat.uci.edu",
            "today.uci.edu/department/information_computer_sciences"
        ]

        ignore_domains = [
        "gitlab.ics.uci.edu",  # Ignore GitLab links specifically
        "cecs.uci.edu"
        ]
        
        if (
            not parsed.scheme in {"http", "https"}
            or parsed.hostname is None
            or parsed.netloc is None
            or "?" in url
            or "&" in url
            or "#" in url
        ):
            return False

        # Ignore specific domains (like GitLab)
        if any(domain in parsed.hostname for domain in ignore_domains):
            return False

        # Match only if the hostname ends with one of the valid domains
        if not any(parsed.hostname.endswith(domain) for domain in valid_domains):
            return False

        if any(fragment in url for fragment in ["redirect", "#comment", "#comments", "#respond"]):
            return False

        # https://support.archive-it.org/hc/en-us/articles/208332963-Modify-crawl-scope-with-a-Regular-Expression#RepeatingDirectories
        if re.match(r"^.*?(/.+?/).*?\1.*$|^.*?/(.+?/)\2.*$", parsed.path.lower()):
            return False 

        if (
            re.search(r"/(search|login|logout|api|admin|raw|static|calendar|event)/", parsed.path.lower())
            or re.search(r"/(page|p)/?\d+", parsed.path.lower())
            or re.search(r"(sessionid|sid|session)=[\w\d]{32}", parsed.query)
            or re.match(
                r".*\.(css|js|bmp|gif|jpe?g|ico|png|tiff?|mid|mp2|mp3|mp4|img"
                r"|wav|apk|war|avi|mov|mpeg|ram|m4v|mkv|ogg|ogv|pdf|ps|eps|tex|ppt|pptx|doc|docx|xls|xlsx"
                r"|data|dat|exe|bz2|tar|msi|bin|7z|psd|dmg|iso|epub|dll|cnf|tgz|sha1"
                r"|thmx|mso|arff|rtf|jar|csv|rm|smil|wmv|swf|wma|zip|rar|gz|mpg|)$",
                parsed.path.lower(),
            )
        ):
            return False
        
        if re.search(
                r"/\d{4}/\d{2}/\d{2}/|/\d{4}-\d{2}-\d{2}/|/(19|20)[0-9]{2}/|/(19|20)[0-9]{2}$|/(19|20)[0-9]{2}-[0-9]{1,2}",
                parsed.path.lower(),
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
    holder += f"1. Number of unique pages found: {len(uniqueURL)}"

    result = longest_page(url_content_dictionary)
    holder += f" \n2. Longest page: {result[0]} with {result[1]} words total\n\n"

    holder += "\n3. 50 most common words in order of most frequent to least frequent are:\n"
    url_tuple = fifty_common_words(url_content_dictionary)
    frequency_list = ""
    for i in range(len(url_tuple)):
        if i == len(url_tuple) - 1:
            frequency_list = frequency_list + url_tuple[i][0] + " -> " + str(url_tuple[i][1]) + " \n "
        else:
            frequency_list = frequency_list + url_tuple[i][0] + " -> " + str(url_tuple[i][1]) + "\n"
        
    holder += frequency_list

    holder += "\n4. The list of all subdomains are: \n"
    subdomainCount.sort(key=lambda x: x[0])

    for subdomain, count in subdomainCount:
        holder += f"{subdomain} has {count} unique subdomains\n"

    # Write holder to a text file
    with open("result.txt", "w") as file:
        file.write(holder)

    print("Result has been written to result.txt file.")