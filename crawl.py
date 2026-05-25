"""HTML parsing utilities for extracting structured data from web pages."""

from typing import TypedDict
from urllib.parse import urlparse

from bs4 import BeautifulSoup, Tag


class PageData(TypedDict):
    """Structured data extracted from a single web page.

    Attributes:
        url: The canonical URL of the page.
        heading: Text of the first h1 or h2 tag, or empty string if absent.
        first_paragraph: Text of the first paragraph (preferring content inside
            <main>), or empty string if absent.
        outgoing_links: Deduplicated list of href values found on the page,
            with relative paths resolved against the page URL.
        image_urls: Deduplicated list of img src values found on the page,
            with relative paths resolved against the page URL.
    """

    url: str
    heading: str
    first_paragraph: str
    outgoing_links: list[str]
    image_urls: list[str]


def normalize_url(url: str) -> str:
    """Strip the scheme from a URL, returning only the host and path.

    Args:
        url: A fully-qualified URL (e.g. ``https://example.com/path``).

    Returns:
        A string of the form ``host/path`` with no scheme or query string.
    """
    parsed = urlparse(url)
    return f"{parsed.netloc}{parsed.path}"


def get_heading(soup: BeautifulSoup) -> str:
    """Return the text of the first h1 or h2 tag in the document.

    Args:
        soup: Parsed representation of the HTML document.

    Returns:
        Stripped text of the first heading tag found, or an empty string if
        neither h1 nor h2 is present.
    """
    h_tag = soup.find("h1") or soup.find("h2")
    return h_tag.get_text(strip=True) if isinstance(h_tag, Tag) else ""


def get_first_paragraph(soup: BeautifulSoup) -> str:
    """Return the text of the first paragraph, preferring content inside <main>.

    Args:
        soup: Parsed representation of the HTML document.

    Returns:
        Stripped text of the first <p> tag found inside <main>, or the first
        <p> anywhere in the document if no <main> is present or <main> has no
        paragraph. Returns an empty string if no paragraph exists.
    """
    main_tag = soup.find("main")
    if isinstance(main_tag, Tag):
        p_tag = main_tag.find("p")
        if isinstance(p_tag, Tag):
            return p_tag.get_text(strip=True)
    p_tag = soup.find("p")
    return p_tag.get_text(strip=True) if isinstance(p_tag, Tag) else ""


def get_urls(soup: BeautifulSoup, base_url: str) -> list[str]:
    """Extract all unique href values from anchor tags in the document.

    Args:
        soup: Parsed representation of the HTML document.
        base_url: Base URL used to resolve relative paths (those starting
            with ``/``).

    Returns:
        Deduplicated list of URLs in document order. Relative paths are
        prepended with ``base_url``; absolute URLs are kept as-is.
    """
    urls: dict[str, None] = {}
    for a_tag in soup.find_all("a", href=True):
        if not isinstance(a_tag, Tag):  # pragma: no cover
            continue
        href = str(a_tag["href"])
        if href.startswith("/"):
            href = base_url + href
        urls[href] = None
    return list(urls)


def get_images(soup: BeautifulSoup, base_url: str) -> list[str]:
    """Extract all unique src values from img tags in the document.

    Args:
        soup: Parsed representation of the HTML document.
        base_url: Base URL used to resolve relative paths (those starting
            with ``/``).

    Returns:
        Deduplicated list of image URLs in document order. Relative paths are
        prepended with ``base_url``; absolute URLs are kept as-is.
    """
    images: dict[str, None] = {}
    for img_tag in soup.find_all("img", src=True):
        if not isinstance(img_tag, Tag):  # pragma: no cover
            continue
        src = str(img_tag["src"])
        if src.startswith("/"):
            src = base_url + src
        images[src] = None
    return list(images)


def extract_page_data(html: str, page_url: str) -> PageData:
    """Parse an HTML page and return all structured data in one call.

    Args:
        html: Raw HTML string to parse.
        page_url: Canonical URL of the page, used to resolve relative links
            and images and stored verbatim in the returned ``url`` field.

    Returns:
        A :class:`PageData` dict containing the URL, heading, first paragraph,
        outgoing links, and image URLs extracted from the page.
    """
    soup = BeautifulSoup(html, "html.parser")
    return {
        "url": page_url,
        "heading": get_heading(soup),
        "first_paragraph": get_first_paragraph(soup),
        "outgoing_links": get_urls(soup, page_url),
        "image_urls": get_images(soup, page_url),
    }
