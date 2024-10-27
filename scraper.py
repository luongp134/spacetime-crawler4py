import re
import sys
from urllib.parse import urlparse, urljoin, urldefrag
import urllib.request
from bs4 import BeautifulSoup
import lxml


subdomains = subdomainTrie
from utils.subdomain import *

visit_count = {}

def scraper(url, resp):

    links = extract_next_links(url, resp)
    return [link for link in links if is_valid(link)]

#After we have finished scraping everything, the way to get the subdomain counts is:

# results = subdomains.subdomainCount()
# results.sort(key=lambda x: x[0])

# for subdomain, count in results:
#     print(f"{subdomain}, {count}")


#After we have finished scraping everything, the way to get the subdomain counts is:

# results = subdomains.subdomainCount()
# results.sort(key=lambda x: x[0])

# for subdomain, count in results:
#     print(f"{subdomain}, {count}")


def extract_next_links(url, resp):
    # Implementation required.
    # url: the URL that was used to get the page
    # resp.url: the actual url of the page
    # resp.status: the status code returned by the server. 200 is OK, you got the page. Other numbers mean that there was some kind of problem.
    # resp.error: when status is not 200, you can check the error here, if needed.
    # resp.raw_response: this is where the page actually is. More specifically, the raw_response has two parts:
    #         resp.raw_response.url: the url, again
    #         resp.raw_response.content: the content of the page!
    # Return a list with the hyperlinks (as strings) scrapped from resp.raw_response.content
    
    hyperlinks = []

    if resp.status != 200 or resp.status == 204: 
        return []
    if not resp.raw_response.content or len(resp.raw_response.content) < 500:
        return []

    try:
        soup = BeautifulSoup(url, 'lxml') #parse html
        
        for element in soup(['script', 'style', 'nav', 'footer', 'header']):
            element.decompose()

        page_text = soup.get_text()
        if len(page_text.strip()) < 1500: #low textual information content
            return []
        
        tokens = tokenize(page_text)

        if len(set(tokens)) < 45: #low unique tokens
            return []


        for a in soup.find_all('a', href=True): #find anchor tags with href
            href = a.get('href')
            if not href: #ignore empty href
                continue
            
            try:
                parsed = urlparse(href) #parse href

                if parsed.scheme and parsed.netloc: #check for scheme and netloc = fullURL
                    fullURL = href
                else:
                    fullURL = urljoin(url,href)

                if fullURL not in hyperlinks: #duplicates
                    hyperlinks.append(fullURL)
            except Exception:
                continue
    except Exception:
        return hyperlinks
    return hyperlinks

def is_valid(url):
    # Decide whether to crawl this url or not.

    # Here is where you will call to add to the link. For example,
    # subdomains.addLink(url)

    # Decide whether to crawl this url or not. 
    # If you decide to crawl it, return True; otherwise return False.
    # There are already some conditions that return False.
    global visit_count

    try:
        url_without_fragment = urldefrag(url).url  # need for defragging of url
        parsed = urlparse(url_without_fragment)
        valid_domains = [
            ".ics.uci.edu",
            "cs.uci.edu",
            ".informatics.uci.edu",
            ".stat.uci.edu",
        ]

        # Preliminary checks for URL scheme, hostname, and query characters
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

        # Exclude URLs that match the following criteria:
        # 1. Include a valid domain from the `valid_domains` list.
        # 2. Do not include certain file extensions or paths indicating non-content URLs.
        # 3. Patterns to exclude low-value paths, infinite pages
        if (
            re.search(
                r"/(search|login|logout|api|admin|raw|static)/", parsed.path.lower()
            ) # low-value path
            or re.search(r"/(page|p)/?\d+", parsed.path.lower())  # infinite pages
            or re.search(r"(sessionid|sid|session)=[\w\d]{32}", parsed.query) # sessionID or random long string
            or re.match(
                r".*\.(css|js|bmp|gif|jpe?g|ico|png|tiff?|mid|mp2|mp3|mp4"
                r"|wav|avi|mov|mpeg|ram|m4v|mkv|ogg|ogv|pdf|ps|eps|tex|ppt|pptx|doc|docx|xls|xlsx"
                r"|data|dat|exe|bz2|tar|msi|bin|7z|psd|dmg|iso|epub|dll|cnf|tgz|sha1"
                r"|thmx|mso|arff|rtf|jar|csv|rm|smil|wmv|swf|wma|zip|rar|gz)$",
                parsed.path.lower(), # end with a specific non-useful set of file extensions
            )
            or re.search(
            r"/\d{4}/\d{2}/\d{2}/|/\d{4}-\d{2}-\d{2}/|\/(19|20)[0-9]{2}/|\/(19|20)[0-9]{2}$|\/(19|20)[0-9]{2}-[0-9]{1,2}",
            parsed.path.lower(), # date-like patterns
        )):
            return False
        return True

    except (ValueError, TypeError) as e:
        print(f"Error for URL {url}: {e}")
        return False


def get_output():
    # returns the answer to all four problems
    # TODO: need other helper function for completion
    holder = ""

    # Question 1: Number of unique pages found
    holder += f"1. Number of unique pages found: <<helper function>>"

    # Question 2: Longest page in terms of number of words
    holder += (
        f"2. Longest page: <<helper function>> with <<helper function>> words total\n\n"
    )

    # Question 3: 50 most common words
    holder += (
        "3. 50 most common words in order of most frequent to least frequent are:\n"
    )

    # Question 4: Subdomains found and total number of subdomains

    # Write holder to a text file
    with open("result.txt", "w") as file:
        file.write(holder)

    print("Result has been written to result.txt file.")

"""
    tokenize: 
    reads each character from the text file one by one,
    checks if alphanumeric, and appends valid characters to list

    Time Complexity:
    O(n), n is the number of characters
    Iterates through each character once, so it runs linear
"""
def tokenize(filePath):
    try:
        with open(filePath, 'r', encoding="utf8") as text:
            token = []
            empty = ''
            while True:
                char = text.read(1)
                if not char:
                    break
                try:
                    if ('a' <= char <= 'z') or ('A' <= char <= 'Z') or ('0' <= char <= '9'):
                        empty += char.lower()
                    else:
                        if empty:
                            token.append(empty)
                            empty = ''
                except Exception as e:
                    print(f"Error processing {char}: {e}")
            if empty:
                token.append(empty)
        return token
    except FileNotFoundError:
        print(f"Error: File '{filePath}' not found.")
        sys.exit(1)
    except Exception as err:
        print(f"An error occurred: {str(err)}")
        sys.exit(1)
