import re
from urllib.parse import urlparse


class Parser:
    @classmethod
    def parse_url(cls, url, domain_check, success_callback, validate_path=True):
        if not isinstance(url, str):
            return "error: no data", None
        
        url = url.strip().lower()
        
        if not domain_check(url):
            return "error: no data", None

        if validate_path:
            paths = urlparse(url).path.split('/')
            if not len(paths) > 1 or not len(paths[1]):
                return "error: no data", None
            elif len(paths[1]) <= 2:
                return f"review: {url}", None
            
        return success_callback(url)

    @classmethod
    def extract_matches(cls, url, pattern):
        matches = re.findall(pattern, url)
        return "success", matches[0] if matches else None

    @classmethod
    def github(cls, url):
        def domain_check(url):
            return 'github.com' in url
        
        def success_callback(url):
            url = url.replace("orgs/","").replace("repositories","").strip("/")
            paths = urlparse(url).path.split('/')
            if len(paths) == 2 and "?" not in paths[1] and paths[1] != "search":
                return "success", paths[1]
            elif len(paths) >= 3 and "?" not in paths[2]:
                return "success", paths[1] + "/" + paths[2]
            return f"review: {url}", None
        
        return cls.parse_url(url, domain_check, success_callback)

    @classmethod
    def etherscan(cls, url):
        def domain_check(url):
            return 'etherscan.io' in url
        
        def success_callback(url):
            if '/txs' in url or '/token' in url:
                return f"review: {url}", None
            eth_address_pattern = r'(0x[a-fA-F0-9]{40})'
            return cls.extract_matches(url, eth_address_pattern)
        
        return cls.parse_url(url, domain_check, success_callback)
    
    @classmethod
    def basescan(cls, url):
        def domain_check(url):
            return 'basescan.org' in url
        
        def success_callback(url):
            if '/txs' in url or '/token' in url:
                return f"review: {url}", None
            eth_address_pattern = r'(0x[a-fA-F0-9]{40})'
            return cls.extract_matches(url, eth_address_pattern)
        
        return cls.parse_url(url, domain_check, success_callback)

    @classmethod
    def npm(cls, url):
        def domain_check(url):
            return 'npmjs.com' in url or 'npm.im' in url or 'npm-stat' in url
        
        def success_callback(url):
            if 'npmjs.com' in url: 
                paths = urlparse(url).path.split('/')
                return "success", "/".join(paths[2:])
            if 'npm.im' in url:
                paths = urlparse(url).path.split('/')
                return "success", "/".join(paths[1:])
            if 'npm-stat' in url:
                package = url.split('?package=')[1].split('&')[0]
                package = package.replace('%40', '@').replace('%2f', '/')
                return "success", package
            return f"review: {url}", None
        
        return cls.parse_url(url, domain_check, success_callback)
    
    @classmethod
    def twitter(cls, url):
        def domain_check(url):
            return 'twitter.com' in url or 'x.com' in url
        
        def success_callback(url):
            paths = urlparse(url).path.split('/')
            if len(paths) >= 2 and paths[1] not in ["search", "home"]:
                return "success", paths[1]
            return f"review: {url}", None
        
        return cls.parse_url(url, domain_check, success_callback)

    @classmethod
    def substack(cls, url):
        def domain_check(url):
            return 'substack.com' in url

        def success_callback(url):
            domain = urlparse(url)
            try:
                subdomain = domain.hostname.split('.')[0]
                return "success", subdomain
            except:
                return f"review: {url} {len(paths)}", None
        
        return cls.parse_url(url, domain_check, success_callback,validate_path=False)
    
    @classmethod
    def optimism_gov(cls, url):
        def domain_check(url):
            return 'gov.optimism.io' in url

        def success_callback(url):
            paths = urlparse(url).path.split('/')
            if len(paths) >= 2 and paths[1] in ["t", "u"]:
                return "success", paths[2]
            return f"review: {url}", None
        
        return cls.parse_url(url, domain_check, success_callback, validate_path=False)

    @classmethod
    def dune(cls, url):
        def domain_check(url):
            return 'dune.com' in url

        def success_callback(url):
            paths = urlparse(url).path.split('/')
            if len(paths) >= 1 and paths[1] not in ["queries", "embeds"]:
                return "success", paths[1]
            return f"review: {url}", None
        
        return cls.parse_url(url, domain_check, success_callback, validate_path=False)

    @classmethod
    def flipside(cls, url):
        def domain_check(url):
            return 'flipsidecrypto.xyz' in url

        def success_callback(url):
            paths = urlparse(url).path.split('/')
            if len(paths) >= 1 and paths[1] not in ["?"]:
                return "success", paths[1]
            return f"review: {url}", None
        
        return cls.parse_url(url, domain_check, success_callback, validate_path=False)


# Usage example:
result, data = Parser.etherscan("https://optimistic.etherscan.io/tx/0xcbae480ab46d58588ab81f3c59551713cd364f5df38e4e6ed917e51f9a2db2bb")