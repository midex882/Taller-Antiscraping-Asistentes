#!/usr/bin/env python3
"""
Dependency‑free simple web crawler for workshop use.

Features:
- Asks for a starting URL.
- Fetches pages, streams their HTML to the console.
- Skips inline CSS between <style> and </style>.
- Extracts <a href="..."> links and follows them with no limits.
- Uses a forgiving regex fallback to catch links in malformed HTML.
- If a non-empty llms.txt is found directly under the given URL
  (URL + "llms.txt"), prints it and stops.
"""

import sys
import time
import re
import urllib.parse
import urllib.request
import urllib.error
from html.parser import HTMLParser
from collections import deque


class LinkExtractor(HTMLParser):
    """
    Basic HTMLParser-based link extractor for reasonably well-formed HTML.
    """
    def __init__(self, base_url):
        super().__init__()
        self.base_url = base_url
        self.links = []

    def handle_starttag(self, tag, attrs):
        if tag.lower() != "a":
            return
        href = None
        for (name, value) in attrs:
            if name.lower() == "href" and value:
                href = value
                break
        if href:
            absolute = urllib.parse.urljoin(self.base_url, href)
            self.links.append(absolute)


def fetch(url):
    """
    Fetch a URL and return (final_url, content_type, text, bytes_length).
    """
    headers = {
        "User-Agent": "SimpleStdlibCrawler/1.2 (+https://example.org/)"
    }
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, timeout=15) as resp:
        final_url = resp.geturl()
        content_type = resp.headers.get("Content-Type", "")
        content_bytes = resp.read()
        try:
            text = content_bytes.decode("utf-8", errors="replace")
        except LookupError:
            text = content_bytes.decode("latin-1", errors="replace")
        return final_url, content_type, text, len(content_bytes)


def extract_links(base_url, html):
    """
    Extract links in a forgiving way:
    - First, use HTMLParser on proper <a href="..."> tags.
    - Then, also regex any href="..." patterns from the raw HTML
      to catch badly formed markup (e.g. Nepenthes).
    """
    parser = LinkExtractor(base_url)
    parser.feed(html)
    links = list(parser.links)

    # Very simple regex fallback: href="..." or href='...'
    for match in re.findall(r'href\s*=\s*["\']([^"\']+)["\']', html, flags=re.IGNORECASE):
        absolute = urllib.parse.urljoin(base_url, match.strip())
        links.append(absolute)

    # Deduplicate while preserving order
    seen = set()
    unique_links = []
    for link in links:
        if link not in seen:
            seen.add(link)
            unique_links.append(link)

    return unique_links


def stream_text(url, html):
    """
    Stream page HTML to stdout line by line, but skip everything
    between <style> and </style>.
    """
    print("=" * 80)
    print(f"[VISITING] {url}")
    print("=" * 80)

    in_style = False

    for raw_line in html.splitlines():
        line = raw_line.rstrip()
        if not line:
            continue

        lower = line.lower()

        # Entering a <style> block
        if "<style" in lower:
            in_style = True
            # If </style> is also on this line, handle only what's after it
            if "</style>" in lower:
                end_pos = lower.rfind("</style>")
                after = line[end_pos + len("</style>"):].strip()
                in_style = False
                if after:
                    print(after)
                    time.sleep(0.005)
            continue

        # Inside <style>, look for closing tag
        if in_style:
            if "</style>" in lower:
                end_pos = lower.rfind("</style>")
                after = line[end_pos + len("</style>"):].strip()
                in_style = False
                if after:
                    print(after)
                    time.sleep(0.005)
            # Skip everything up to </style>
            continue

        # Normal streaming outside <style> blocks
        print(line)
        time.sleep(0.005)

    print("\n[END OF PAGE]\n")


def try_llms_txt(url):
    """
    Check for llms.txt directly under the given URL:
    e.g. if url is http://example.com/foo, check http://example.com/foo/llms.txt
    If found and looks like a non-empty text file, print it and return True.
    Otherwise return False.
    """
    # Ensure trailing slash so joining behaves as "under this path"
    if not url.endswith("/"):
        base = url + "/"
    else:
        base = url

    llms_url = urllib.parse.urljoin(base, "llms.txt")
    print(f"[INFO] Checking for llms.txt at {llms_url}")

    try:
        final_url, content_type, text, size = fetch(llms_url)
        if "text" not in content_type.lower() or not text.strip():
            print("[INFO] llms.txt not in expected text format, ignoring.")
            return False

        print("\n" + "#" * 80)
        print(f"[FOUND] llms.txt at {final_url} ({size} bytes)")
        print("#" * 80 + "\n")
        print(text)
        print("\n" + "#" * 80)
        print("[INFO] Stopping crawl because llms.txt was found and read.")
        print("#" * 80 + "\n")

        return True

    except (urllib.error.URLError, urllib.error.HTTPError):
        print("[INFO] No accessible llms.txt found at this URL.")
        return False

    


def crawl(start_url, check_llms):
    # First, check for llms.txt under the given URL (optionally)
    if check_llms:
        if try_llms_txt(start_url):
            return

    queue = deque([start_url])

    while queue:
        url = queue.popleft()

        try:
            final_url, content_type, text, size = fetch(url)
        except (urllib.error.URLError, urllib.error.HTTPError) as e:
            print(f"[ERROR] Failed to fetch {url}: {e}", file=sys.stderr)
            continue

        # Skip clearly non-HTML types by content-type header
        ct_lower = content_type.lower()
        if "text/css" in ct_lower:
            print(f"[SKIP] {final_url} (Content-Type: {content_type})")
            continue
        if ("html" not in ct_lower and
            "xml" not in ct_lower and
            "text" not in ct_lower):
            print(f"[SKIP] {final_url} (Content-Type: {content_type})")
            continue

        print(f"[INFO] Fetched {final_url} ({size} bytes, {content_type})")
        stream_text(final_url, text)

        links = extract_links(final_url, text)
        print(f"[INFO] Found {len(links)} links on {final_url}")
        for link in links:
            parsed = urllib.parse.urlparse(link)
            if parsed.scheme in ("http", "https"):
                # Intentionally NO visited set: revisit URLs indefinitely
                queue.append(link)

        time.sleep(0.5)

    # First, check for llms.txt under the given URL
    if try_llms_txt(start_url):
        return

    queue = deque([start_url])

    while queue:
        url = queue.popleft()

        try:
            final_url, content_type, text, size = fetch(url)
        except (urllib.error.URLError, urllib.error.HTTPError) as e:
            print(f"[ERROR] Failed to fetch {url}: {e}", file=sys.stderr)
            continue

        # Skip clearly non-HTML types by content-type header
        ct_lower = content_type.lower()
        if "text/css" in ct_lower:
            print(f"[SKIP] {final_url} (Content-Type: {content_type})")
            continue
        if ("html" not in ct_lower and
            "xml" not in ct_lower and
            "text" not in ct_lower):
            print(f"[SKIP] {final_url} (Content-Type: {content_type})")
            continue

        print(f"[INFO] Fetched {final_url} ({size} bytes, {content_type})")
        stream_text(final_url, text)

        links = extract_links(final_url, text)
        print(f"[INFO] Found {len(links)} links on {final_url}")
        for link in links:
            parsed = urllib.parse.urlparse(link)
            if parsed.scheme in ("http", "https"):
                # Intentionally NO visited set: revisit URLs indefinitely
                queue.append(link)

        time.sleep(0.5)


def main():

    ANSI_YELLOW = "\033[90m"
    ANSI_CYAN = "\033[91m"
    ANSI_WHITE = "\033[0m"

    print("Press Ctrl+C to stop.\n")

    print(ANSI_YELLOW + """                                                                                                    
                                                                                                    
                                                                ░                                   
                                                                ░                                   
                        ░                                       ░          ░                        
                        ░░      ░                               ░░        ░░                        
                         ░░     ░                      ░░       ░░      ░░░   ░                     
              ░░░░        ▒░    ░▒        ░             ░░     ░▓▒▒▒▒███▒▒░   ░   ░                 
                 ░▒█▓▒▒▒██▓▒▒░  ░▒      ░░          ░  ░░░░ ░░▒██▒░░▒▒█▒▒░▒███▒    ░                
                ░▒▓▓▒▒░░ ░░░▒▒▓▓▓▒     ░░░░ ░░░      ░░   ▒▒░░░░▒▓▒░▓██░░░▓█▓▒▒▒░ ░▒                
              ░▒▒▓▒░░▒▓█▓░░░░▒░░░▒▒░  ░░ ░░ ░░ ░     ░▒░░▒█▓░░░░▒██▓██▓▓▒▓█▓▒▒▒███▒  ░              
           ░▒▒██▓▒▒▓█▓▓██▓▓▓██░░░░█▓█▒░  ░░ ░░ ░░   ░░░▒▒▒▒░░▒▒▓▓▓█▓▓█▓▒▓█▓▓▒▓██▓▓▒░ ▒              
          ▒▒▒▒▒▒██▓▓▒▒▒░░▒▒▓█▓▓▓██▓▒▒▒▒▒░░░ ░░  ░   ░▒▒█▓░  ░████▓░▒░░▒░░▒▒▓██▓▒▒▓▓█▒▒              
        ░░░░▓▓▒▒▒▒▓░ ▒░ ░░ ░▒▒▓██▓░░░░▓▓▒▒▒▒▒░░ ░░░▓▒░░░░▒░▒▒▓▓▒░░▒░▒▒ ░░ ░▒▒▓███████░░             
        ░  ▒▓▓▓▒░░▒ ░░ ░░ ░░   ▒▓▓▒▒▒▓▒░░▒▓▓▒▒▒▓▓▒▒█▒░░░░░████▒░   ░▒░░░ ░░ ░█▓▓▒▒▒▒▒░  ░           
       ░  ▒▒▒▒▒░░▒░ ▒ ░▒░░    ░░░▒▒▓██▒░░░▒░░░░░▒░░░ ░░▒▓▒▒▒░ ░░░   ░▒  ░ ░▒░░▒▓▓▓▓█▓░░▒░           
         ░▒░▒▒░ ▒░  ░ ░░░   ░░░    ▒█▓▒▒▒██▒░░░░▒░░▒▒████▒░     ░    ░ ░░░░░░▒▓▓▓▓▓██▓░▒            
         ▒▒░▒▒  ░░   ░░   ░░        ░░░▒▒██▓▒▒▓▓██▓▒▓▒▓▒░▒░            ░  ▒░ ░███▓██▒░ ▒            
         ▒▒ ▒▒   ░                 ░░     ░▒░▒░░▒▓▒▒░     ░░            ░░ ░▒▒▒▒▒▒▓██▓▒             
         ░▒ ░▒                    ░░      ░░       ░░      ░░             ▒░░██▓▓▒▓▒░               
          ▒░ ▒░                   ░      ░░        ░░                    ▒░▒▓▓▓▓▓███░               
           ░░ ░░                 ░      ░░          ░                    ░░░▓▓▓▓▓▓█▓▒░              
                ░░                      ░            ░                   ░░▓▓▓▒▒▓▓▓█░░              
                                                                          ░▓▓▓▓▓▓▓▓█░               
                                                                           ▒▓▓▓▓▓██▒                
            ██╗    ██╗███████╗██████╗                                        ▒▓▓▓▓                  
            ██║    ██║██╔════╝██╔══██╗                                      ░▓░  ▒▓                 
            ██║ █╗ ██║█████╗  ██████╔╝                                      ▒▒     ▓                
            ██║███╗██║██╔══╝  ██╔══██╗                                      ▒░      ▒               
            ╚███╔███╔╝███████╗██████╔╝                                      ▒░       ▒              
            ╚══╝╚══╝ ╚══════╝╚═════╝                                        ▒        ░              
                                                                           ░          ░""")


    print(ANSI_CYAN + """                         ██████╗██████╗  █████╗ ██╗    ██╗██╗     ███████╗██████╗
                        ██╔════╝██╔══██╗██╔══██╗██║    ██║██║     ██╔════╝██╔══██╗
                        ██║     ██████╔╝███████║██║ █╗ ██║██║     █████╗  ██████╔╝
                        ██║     ██╔══██╗██╔══██║██║███╗██║██║     ██╔══╝  ██╔══██╗
                        ╚██████╗██║  ██║██║  ██║╚███╔███╔╝███████╗███████╗██║  ██║
                         ╚═════╝╚═╝  ╚═╝╚═╝  ╚═╝ ╚══╝╚══╝ ╚══════╝╚══════╝╚═╝  ╚═╝""")



    print(ANSI_WHITE + "Simple Infinite Web Crawler")
    print("Press Ctrl+C to stop.\n")

    start_url = input("Enter a starting URL (e.g. http://localhost:8893/): ").strip()
    if not start_url:
        print("No URL provided, exiting.")
        return

    # Ask whether to look for llms.txt
    choice = input("Look for llms.txt under this URL? [y/N]: ").strip().lower()
    check_llms = choice == "y"

    parsed = urllib.parse.urlparse(start_url)
    if not parsed.scheme:
        start_url = "http://" + start_url

    try:
        crawl(start_url, check_llms)
    except KeyboardInterrupt:
        print("\n[INFO] Stopped by user.")


if __name__ == "__main__":
    main()