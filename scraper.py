import re
from urllib.parse import urlparse, urldefrag

visit_count = dict()


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
    return list()


def is_valid(url):
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
