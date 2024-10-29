class trieNode:
    def __init__(self):
        self.children = {}

class subdomainTrie:
    def __init__(self):
        self.root = trieNode()
        self.addStarterDomains(['uci'])

    def addStarterDomains(self, domains):
        for domain in domains:
            if domain not in self.root.children:
                self.root.children[domain] = trieNode()

    def addLink(self, link):
        # Split the subdomains 
        # a.ics.uci.edu -> [a, ics, uci, edu]
        # then i start at uci and work backwards
        
        if not any(domain in link for domain in [".ics.uci.edu", ".cs.uci.edu", ".informatics.uci.edu", ".stat.uci.edu", "today.uci.edu/department/information_computer_sciences"]):
            return
        
        preFragmentation = link.split('/')
        subdomains = preFragmentation[2].split('.')[::-1]
        current = self.root

        for subdomain in subdomains:
            if subdomain not in current.children:
                current.children[subdomain] = trieNode()
            current = current.children[subdomain]

    def subdomainCount(self, node=None, prefix="", results=None):
        if node is None:
            node = self.root
        if results is None:
            results = []

        # Iterate over one of the subdomains found
        for part, children in node.children.items():
            entireDomain = f"{part}.{prefix}" if prefix else part

            if children.children:
                # Count the unique subdomains (children)
                unique_count = len(children.children)
                results.append((entireDomain, unique_count))

            # Recursively count for child nodes
            self.subdomainCount(children, entireDomain, results)

        return results  # Return the collected results
    
    def checkIfVisited(self, link):
        preFragmentation = link.split('/')
        subdomains = preFragmentation[2].split('.')[::-1]
        current = self.root
        for subdomain in subdomains:
            if subdomain in current.children:
                current = current.children[subdomain]
            else:
                return True
        return False
        

# trie = subdomainTrie()
# trie.addLink("https://a.ics.uci.edu/#a")
# trie.addLink("https://a.ics.uci.edu/#b")
# trie.addLink("https://a.ics.uci.edu/#asdasdasd")
# trie.addLink("https://a.a.a.a.a.ics.uci.edu")
# trie.addLink("https://b.ics.uci.edu")
# trie.addLink("https://a.ics.uci.edu")
# trie.addLink("https://b.ics.uci.edu")
# trie.addLink("https://b.cs.uci.edu")
# trie.addLink("https://informatics.uci.edu")
# trie.addLink("https://stat.uci.edu")

# print(str(trie.checkIfVisited('https://a.ics.uci.edu/#a')) + '\n')
# print(str(trie.checkIfVisited('https://awhdkjawhdkj.ics.uci.edu/#12736')))

# results = trie.subdomainCount()
# results.sort(key=lambda x: x[0])

# for subdomain, count in results:
#     print(f"{subdomain}, {count}")
