import html
import re
import urllib.parse
import urllib.request


SEARCH_URL = "https://html.duckduckgo.com/html/?q={}"


def clean_result_url(url):
    """Extract the real destination URL from search-engine redirects."""

    url = html.unescape(url)

    for _ in range(5):
        parsed = urllib.parse.urlparse(url)
        query = urllib.parse.parse_qs(parsed.query)

        found = False

        # Common redirect parameters
        for key in ("uddg", "u3", "u", "url", "target"):
            if key in query and query[key]:
                candidate = query[key][0]
                candidate = html.unescape(
                    urllib.parse.unquote(candidate)
                )

                if candidate.startswith("http"):
                    url = candidate
                    found = True
                    break

        if not found:
            break

    return url


def search_web(query, max_results=5):
    """
    Search the web using DuckDuckGo's HTML results.
    """

    query = query.strip()

    if not query:
        return "Please provide something to search for."

    try:
        encoded_query = urllib.parse.quote_plus(query)
        url = SEARCH_URL.format(encoded_query)

        request = urllib.request.Request(
            url,
            headers={
                "User-Agent": (
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 Chrome/131.0 Safari/537.36"
                )
            }
        )

        with urllib.request.urlopen(request, timeout=15) as response:
            page = response.read().decode(
                "utf-8",
                errors="ignore"
            )

        results = []

        blocks = re.findall(
            r'<div[^>]*class="[^"]*result[^"]*"[^>]*>(.*?)</div>\s*</div>',
            page,
            flags=re.IGNORECASE | re.DOTALL
        )

        for block in blocks:

            title_match = re.search(
                r'class="result__a"[^>]*href="([^"]+)"[^>]*>(.*?)</a>',
                block,
                flags=re.IGNORECASE | re.DOTALL
            )

            if not title_match:
                continue

            link = clean_result_url(title_match.group(1))

            title = re.sub(
                r"<.*?>",
                "",
                title_match.group(2)
            )

            title = html.unescape(title).strip()

            snippet_match = re.search(
                r'class="result__snippet"[^>]*>(.*?)</a?>',
                block,
                flags=re.IGNORECASE | re.DOTALL
            )

            if not snippet_match:
                snippet_match = re.search(
                    r'class="result__snippet"[^>]*>(.*?)</div>',
                    block,
                    flags=re.IGNORECASE | re.DOTALL
                )

            snippet = ""

            if snippet_match:
                snippet = re.sub(
                    r"<.*?>",
                    "",
                    snippet_match.group(1)
                )

                snippet = html.unescape(
                    snippet
                ).strip()

            results.append(
                {
                    "title": title,
                    "link": link,
                    "snippet": snippet
                }
            )

            if len(results) >= max_results:
                break

        if not results:
            return f"I couldn't find web results for: {query}"

        lines = [
            f"Web results for: {query}",
            ""
        ]

        for index, result in enumerate(results, start=1):

            lines.append(
                f"{index}. {result['title']}"
            )

            if result["snippet"]:
                lines.append(
                    f"   {result['snippet']}"
                )

            lines.append(
                f"   {result['link']}"
            )

            lines.append("")

        return "\n".join(lines).strip()

    except urllib.error.URLError:
        return (
            "I couldn't connect to the internet "
            "to perform the search."
        )

    except Exception as error:
        return f"Web search error: {error}"