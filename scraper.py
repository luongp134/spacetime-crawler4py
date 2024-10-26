import re
import sys
from urllib.parse import urlparse, urljoin
import urllib.request
from bs4 import BeautifulSoup
import lxml



def scraper(url, resp):
    links = extract_next_links(url, resp)
    return [link for link in links if is_valid(link)]

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
    # If you decide to crawl it, return True; otherwise return False.
    # There are already some conditions that return False.
    try:
        parsed = urlparse(url)
        if parsed.scheme not in set(["http", "https"]):
            return False
        if re.search(r"/\d{4}/\d{2}/\d{2}/", parsed.path): #calendar/dates
            return False
        if re.search(r"/(search|login|logout|api|admin|raw|static)/", parsed.path.lower()): #low value path
            return False
        if re.search(r"/(page|p)/?\d+", parsed.path.lower()): #infinite pages
            return False
        if re.search(r"(sessionid|sid|session)=[\w\d]{32}", parsed.query): #sessionID / random long str.
            return False
        
        return not re.match(
            r".*\.(css|js|bmp|gif|jpe?g|ico"
            + r"|png|tiff?|mid|mp2|mp3|mp4"
            + r"|wav|avi|mov|mpeg|ram|m4v|mkv|ogg|ogv|pdf"
            + r"|ps|eps|tex|ppt|pptx|doc|docx|xls|xlsx|names"
            + r"|data|dat|exe|bz2|tar|msi|bin|7z|psd|dmg|iso"
            + r"|epub|dll|cnf|tgz|sha1"
            + r"|thmx|mso|arff|rtf|jar|csv"
            + r"|rm|smil|wmv|swf|wma|zip|rar|gz)$", parsed.path.lower())


    except TypeError:
        print ("TypeError for ", parsed)
        raise

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
