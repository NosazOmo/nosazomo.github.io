"""Rebuilds the "how i think" article list in index.html from the Substack feed.
Run hourly by .github/workflows/substack.yml. Only the block between
<!-- ARTICLES:START --> and <!-- ARTICLES:END --> is replaced."""
import html, re, sys, urllib.request
import xml.etree.ElementTree as ET
from email.utils import parsedate_to_datetime

FEED = "https://kingzeme.substack.com/feed"
PAGE = "index.html"

def load_feed(source):
    if source.startswith("http"):
        req = urllib.request.Request(source, headers={"User-Agent": "nosa-website-feed-updater"})
        with urllib.request.urlopen(req, timeout=30) as r:
            return r.read()
    return open(source, "rb").read()

def build_list(xml_bytes):
    root = ET.fromstring(xml_bytes)
    items = []
    for it in root.iter("item"):
        title = (it.findtext("title") or "").strip()
        link = (it.findtext("link") or "").strip()
        date = parsedate_to_datetime(it.findtext("pubDate"))
        if title and link:
            items.append((date, title, link))
    items.sort(reverse=True)
    rows = []
    for date, title, link in items:
        rows.append(
            '      <li><a href="%s" target="_blank" rel="noopener">%s</a><time datetime="%s">%s</time></li>'
            % (html.escape(link, quote=True), html.escape(title), date.strftime("%Y-%m-%d"),
               date.strftime("%b ") + str(date.day) + date.strftime(", %Y")))
    return '    <ol class="articles" id="articles">\n' + "\n".join(rows) + "\n    </ol>\n"

def main():
    source = sys.argv[1] if len(sys.argv) > 1 else FEED
    new_list = build_list(load_feed(source))
    page = open(PAGE, encoding="utf-8").read()
    pattern = re.compile(r"(<!-- ARTICLES:START -->\n)(.*?)(    <!-- ARTICLES:END -->)", re.S)
    if not pattern.search(page):
        sys.exit("article markers not found in index.html")
    updated = pattern.sub(lambda m: m.group(1) + new_list + m.group(3), page, count=1)
    if updated != page:
        open(PAGE, "w", encoding="utf-8").write(updated)
        print("article list updated")
    else:
        print("no new articles")

if __name__ == "__main__":
    main()
