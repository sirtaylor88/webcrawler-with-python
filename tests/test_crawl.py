"""Tests for the crawl module's HTML parsing utilities."""

from unittest.mock import MagicMock, patch

import pytest
import requests as req

from bs4 import BeautifulSoup

from crawl import (
    extract_page_data,
    get_first_paragraph,
    get_heading,
    get_html,
    get_images,
    get_urls,
    normalize_url,
)


def test_get_html_returns_text() -> None:
    """Returns the response body text on a successful request."""
    with patch("crawl.requests.get") as mock_get:
        mock_response = MagicMock()
        mock_response.text = "<html><body>Hello</body></html>"
        mock_get.return_value = mock_response
        result = get_html("https://example.com")
    assert result == "<html><body>Hello</body></html>"
    mock_response.raise_for_status.assert_called_once()


def test_get_html_raises_on_http_error() -> None:
    """Propagates an HTTP error raised by raise_for_status."""
    with patch("crawl.requests.get") as mock_get:
        mock_response = MagicMock()
        mock_response.raise_for_status.side_effect = req.HTTPError("404")
        mock_get.return_value = mock_response
        with pytest.raises(req.HTTPError):
            get_html("https://example.com/missing")


def test_normalize_url() -> None:
    """Strips scheme from a URL, keeping host and path."""
    actual = normalize_url("https://www.boot.dev/blog/path")
    assert actual == "www.boot.dev/blog/path"


def test_get_heading_basic() -> None:
    """Extracts text from the first h1 tag."""
    soup = BeautifulSoup("<html><body><h1>Test Title</h1></body></html>", "html.parser")
    assert get_heading(soup) == "Test Title"


def test_get_first_paragraph_main_priority() -> None:
    """Prefers the first paragraph inside <main> over one outside it."""
    html = """<html><body>
        <p>Outside paragraph.</p>
        <main>
            <p>Main paragraph.</p>
        </main>
    </body></html>"""
    assert get_first_paragraph(BeautifulSoup(html, "html.parser")) == "Main paragraph."


def test_get_first_paragraph_no_main() -> None:
    """Falls back to the first paragraph in the document when no <main> exists."""
    html = """<html><body>
        <p>Outside paragraph.</p>
    </body></html>"""
    assert (
        get_first_paragraph(BeautifulSoup(html, "html.parser")) == "Outside paragraph."
    )


def test_get_urls_absolute() -> None:
    """Returns absolute href values unchanged."""
    base = "https://crawler-test.com"
    html = '<html><body><a href="https://crawler-test.com"><span>Boot.dev</span></a></body></html>'
    assert get_urls(BeautifulSoup(html, "html.parser"), base) == [
        "https://crawler-test.com"
    ]


def test_get_urls_no_links() -> None:
    """Returns an empty list when the page has no anchor tags."""
    base = "https://crawler-test.com"
    html = "<html><body><p>No links here.</p></body></html>"
    assert get_urls(BeautifulSoup(html, "html.parser"), base) == []


def test_get_images_relative() -> None:
    """Resolves relative src paths against the base URL."""
    base = "https://crawler-test.com"
    html = '<html><body><img src="/logo.png" alt="Logo"></body></html>'
    assert get_images(BeautifulSoup(html, "html.parser"), base) == [
        "https://crawler-test.com/logo.png"
    ]


def test_get_images_no_images() -> None:
    """Returns an empty list when the page has no img tags."""
    base = "https://crawler-test.com"
    html = "<html><body><p>No images here.</p></body></html>"
    assert get_images(BeautifulSoup(html, "html.parser"), base) == []


def test_get_images_absolute() -> None:
    """Returns absolute src values unchanged."""
    base = "https://crawler-test.com"
    html = '<html><body><img src="https://crawler-test.com/logo.png" alt="Logo"></body></html>'
    assert get_images(BeautifulSoup(html, "html.parser"), base) == [
        "https://crawler-test.com/logo.png"
    ]


def test_get_images_no_src() -> None:
    """Ignores img tags that have no src attribute."""
    base = "https://crawler-test.com"
    html = '<html><body><img alt="No src"></body></html>'
    assert get_images(BeautifulSoup(html, "html.parser"), base) == []


def test_extract_page_data_basic() -> None:
    """Extracts all fields from a well-formed page."""
    url = "https://crawler-test.com"
    html = """<html><body>
        <h1>Test Title</h1>
        <p>This is the first paragraph.</p>
        <a href="/link1">Link 1</a>
        <img src="/image1.jpg" alt="Image 1">
    </body></html>"""
    assert extract_page_data(html, url) == {
        "url": url,
        "heading": "Test Title",
        "first_paragraph": "This is the first paragraph.",
        "outgoing_links": ["https://crawler-test.com/link1"],
        "image_urls": ["https://crawler-test.com/image1.jpg"],
    }


def test_extract_page_data_no_heading() -> None:
    """Returns an empty string for heading when no h1/h2 is present."""
    url = "https://crawler-test.com"
    html = """<html><body>
        <p>This is the first paragraph.</p>
        <a href="/link1">Link 1</a>
        <img src="/image1.jpg" alt="Image 1">
    </body></html>"""
    assert extract_page_data(html, url) == {
        "url": url,
        "heading": "",
        "first_paragraph": "This is the first paragraph.",
        "outgoing_links": ["https://crawler-test.com/link1"],
        "image_urls": ["https://crawler-test.com/image1.jpg"],
    }


def test_extract_page_data_no_paragraph() -> None:
    """Returns an empty string for first_paragraph when no p tag is present."""
    url = "https://crawler-test.com"
    html = """<html><body>
        <h1>Test Title</h1>
        <a href="/link1">Link 1</a>
        <img src="/image1.jpg" alt="Image 1">
    </body></html>"""
    assert extract_page_data(html, url) == {
        "url": url,
        "heading": "Test Title",
        "first_paragraph": "",
        "outgoing_links": ["https://crawler-test.com/link1"],
        "image_urls": ["https://crawler-test.com/image1.jpg"],
    }


def test_extract_page_data_no_links_or_images() -> None:
    """Returns empty lists for outgoing_links and image_urls when none are present."""
    url = "https://crawler-test.com"
    html = """<html><body>
        <h1>Test Title</h1>
        <p>This is the first paragraph.</p>
    </body></html>"""
    assert extract_page_data(html, url) == {
        "url": url,
        "heading": "Test Title",
        "first_paragraph": "This is the first paragraph.",
        "outgoing_links": [],
        "image_urls": [],
    }


def test_extract_page_data_empty_html() -> None:
    """Returns empty strings and lists for all fields when given empty HTML."""
    url = "https://crawler-test.com"
    assert extract_page_data("", url) == {
        "url": url,
        "heading": "",
        "first_paragraph": "",
        "outgoing_links": [],
        "image_urls": [],
    }


def test_extract_page_data_no_main_paragraph() -> None:
    """Falls back to a top-level p tag when <main> exists but contains no paragraph."""
    url = "https://crawler-test.com"
    html = """<html><body>
        <h1>Test Title</h1>
        <main></main>
        <p>This is the first paragraph.</p>
    </body></html>"""
    assert extract_page_data(html, url) == {
        "url": url,
        "heading": "Test Title",
        "first_paragraph": "This is the first paragraph.",
        "outgoing_links": [],
        "image_urls": [],
    }


def test_extract_page_data_multiple_links_and_images() -> None:
    """Collects all links and images in document order."""
    url = "https://crawler-test.com"
    html = """<html><body>
        <h1>Test Title</h1>
        <p>This is the first paragraph.</p>
        <a href="/link1">Link 1</a>
        <a href="/link2">Link 2</a>
        <img src="/image1.jpg" alt="Image 1">
        <img src="/image2.jpg" alt="Image 2">
    </body></html>"""
    assert extract_page_data(html, url) == {
        "url": url,
        "heading": "Test Title",
        "first_paragraph": "This is the first paragraph.",
        "outgoing_links": [
            "https://crawler-test.com/link1",
            "https://crawler-test.com/link2",
        ],
        "image_urls": [
            "https://crawler-test.com/image1.jpg",
            "https://crawler-test.com/image2.jpg",
        ],
    }


def test_extract_page_data_nested_elements() -> None:
    """Extracts data correctly when links and images are inside <main>."""
    url = "https://crawler-test.com"
    html = """<html><body>
        <h1>Test Title</h1>
        <main>
            <p>This is the first paragraph.</p>
            <a href="/link1">Link 1</a>
            <img src="/image1.jpg" alt="Image 1">
        </main>
    </body></html>"""
    assert extract_page_data(html, url) == {
        "url": url,
        "heading": "Test Title",
        "first_paragraph": "This is the first paragraph.",
        "outgoing_links": ["https://crawler-test.com/link1"],
        "image_urls": ["https://crawler-test.com/image1.jpg"],
    }
