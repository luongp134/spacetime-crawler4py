import re
from urllib.parse import urlparse, urldefrag


visit_count = dict()

def scraper(url, resp):

    links = extract_next_links(url, resp)

    # Call getOutput() only if frontier is empty
    if frontier_empty:
        get_output()
        frontier_empty = False
    
    # checks the list of urls found on a page using the is_valid function to
    # decide whether or not to return each url
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
    return list()

def is_valid(url):
    # Decide whether to crawl this url or not. 
    # If you decide to crawl it, return True; otherwise return False.
    # There are already some conditions that return False.
    global visit_count
    
    try:
        url_without_fragment = urldefrag(url).url # need for defragging of url
        parsed = urlparse(url_without_fragment)
        validDomains=[".ics.uci.edu","cs.uci.edu",".informatics.uci.edu",".stat.uci.edu"]
        if parsed.hostname == None or parsed.netloc == None:
            return False
        if parsed.scheme not in set(["http", "https"]) or (url.find("?") != -1)\
                or (url.find("&") != -1):
            return False
        
        # Exclude URLs that match the following criteria:
        # 1. Include a valid domain from the `validDomains` list.
        # 2. Do not include certain file extensions or paths indicating non-content URLs.
        # 3. Do not include months or mentioned of calendar in the URLs 
        # 4. Do not match certain date or event-related patterns **REMOVED FOR TESTING**.
        # r"|names|epub|csv|page"
        if any(domain in parsed.hostname for domain in validDomains) \
                and not re.search(r"(css|js|bmp|gif|jpe?g|ico"
                                r"|png|tiff?|mid|mp2|mp3|mp4"
                                r"|wav|avi|mov|mpeg|ram|m4v|mkv|ogg|ogv|pdf"
                                r"|ps|eps|tex|ppt|pptx|doc|docx|xls|xlsx"
                                r"|data|dat|exe|bz2|tar|msi|bin|7z|psd|dmg|iso"
                                r"|dll|cnf|tgz|sha1|php|z|odc|calendar|archive"
                                r"|thmx|mso|arff|rtf|jar|docs|bib|events|event|date"
                                r"|rm|smil|wmv|swf|wma|zip|rar|gz)",
                                parsed.path.lower())\
                and not re.match(r'\/(19|20)[0-9]{2}/|\/(19|20)[0-9]{2}$|\/(19|20)'
                                r'[0-9]{2}-[0-9]{1,2}|\/[0-9]{1,2}-(19|20)[0-9]{2}|'
                                r'[0-9]{1,2}-[0-9]{1,2}-(19|20)[0-9]{2}'
                                r'/\d{4}-\d{2}-\d{2}/', parsed.path.lower()):

            if url_without_fragment in visit_count and visit_count[url_without_fragment] >= 3:
                return False  # Do not crawl if already visited more than 3 times
        else:
            return False

    except ValueError as e:
        print(f'Error validating IP address for URL: {url}. Error: {e}')
        return False

    except TypeError:
        print ("TypeError for ", parsed)
        raise

def get_output():
    # returns the answer to all four problems 
    # TODO: need other helper function for completion
    holder = ""
    
    # Question 1: Number of unique pages found
    holder += f"1. Number of unique pages found: <<helper function>>"

    # Question 2: Longest page in terms of number of words
    holder += f"2. Longest page: <<helper function>> with <<helper function>> words total\n\n"

    # Question 3: 50 most common words
    holder += "3. 50 most common words in order of most frequent to least frequent are:\n"

    # Question 4: Subdomains found and total number of subdomains

    # Write holder to a text file
    with open("result.txt", "w") as file:
        file.write(holder)

    print("Result has been written to result.txt file.")