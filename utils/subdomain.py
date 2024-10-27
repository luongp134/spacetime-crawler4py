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
        subdomains = link.split('.')[::-1]
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


#This is an example implementation

# trie = subdomainTrie()
# trie.addLink("a.ics.uci.edu")
# trie.addLink("a.a.a.a.a.ics.uci.edu")
# trie.addLink("b.ics.uci.edu")
# trie.addLink("a.ics.uci.edu")
# trie.addLink("b.ics.uci.edu")
# trie.addLink("b.cs.uci.edu")
# trie.addLink("informatics.uci.edu")
# trie.addLink("stat.uci.edu")

# results = trie.subdomainCount()
# results.sort(key=lambda x: x[0])

# for subdomain, count in results:
#     print(f"{subdomain}, {count}")
