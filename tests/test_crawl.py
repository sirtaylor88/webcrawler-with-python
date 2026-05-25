"""Tests for the crawl module's HTML parsing utilities."""

from unittest.mock import MagicMock, patch

import pytest
import requests as req

from bs4 import BeautifulSoup

from crawl import (
    PageData,
    extract_page_data,
    get_first_paragraph,
    get_heading,
    get_html,
    get_images,
    get_urls,
    normalize_url,
)

BASE_URL = "https://crawler-test.com"


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
    assert normalize_url("https://www.boot.dev/blog/path") == "www.boot.dev/blog/path"


def test_get_heading_basic() -> None:
    """Extracts text from the first h1 tag."""
    soup = BeautifulSoup("<html><body><h1>Test Title</h1></body></html>", "html.parser")
    assert get_heading(soup) == "Test Title"


@pytest.mark.parametrize(
    "html,expected",
    [
        pytest.param(
            """<html><body>
        <p>Outside paragraph.</p>
        <main><p>Main paragraph.</p></main>
    </body></html>""",
            "Main paragraph.",
            id="prefers_main",
        ),
        pytest.param(
            "<html><body><p>Outside paragraph.</p></body></html>",
            "Outside paragraph.",
            id="fallback_no_main",
        ),
    ],
)
def test_get_first_paragraph(html: str, expected: str) -> None:
    """Extracts first paragraph with and without a <main> element."""
    assert get_first_paragraph(BeautifulSoup(html, "html.parser")) == expected


@pytest.mark.parametrize(
    "html,expected",
    [
        pytest.param(
            '<html><body><a href="https://crawler-test.com">Boot.dev</a></body></html>',
            ["https://crawler-test.com"],
            id="absolute",
        ),
        pytest.param(
            "<html><body><p>No links here.</p></body></html>",
            [],
            id="no_links",
        ),
    ],
)
def test_get_urls(html: str, expected: list[str]) -> None:
    """Returns href values resolved against the base URL."""
    assert get_urls(BeautifulSoup(html, "html.parser"), BASE_URL) == expected


@pytest.mark.parametrize(
    "html,expected",
    [
        pytest.param(
            '<html><body><img src="/logo.png" alt="Logo"></body></html>',
            ["https://crawler-test.com/logo.png"],
            id="relative",
        ),
        pytest.param(
            "<html><body><p>No images here.</p></body></html>",
            [],
            id="no_images",
        ),
        pytest.param(
            '<html><body><img src="https://crawler-test.com/logo.png" alt="Logo"></body></html>',
            ["https://crawler-test.com/logo.png"],
            id="absolute",
        ),
        pytest.param(
            '<html><body><img alt="No src"></body></html>',
            [],
            id="no_src",
        ),
    ],
)
def test_get_images(html: str, expected: list[str]) -> None:
    """Returns image src values resolved against the base URL."""
    assert get_images(BeautifulSoup(html, "html.parser"), BASE_URL) == expected


@pytest.mark.parametrize(
    "html,expected",
    [
        pytest.param(
            """<html><body>
        <h1>Test Title</h1>
        <p>This is the first paragraph.</p>
        <a href="/link1">Link 1</a>
        <img src="/image1.jpg" alt="Image 1">
    </body></html>""",
            PageData(
                url=BASE_URL,
                heading="Test Title",
                first_paragraph="This is the first paragraph.",
                outgoing_links=[f"{BASE_URL}/link1"],
                image_urls=[f"{BASE_URL}/image1.jpg"],
            ),
            id="basic",
        ),
        pytest.param(
            """<html><body>
        <p>This is the first paragraph.</p>
        <a href="/link1">Link 1</a>
        <img src="/image1.jpg" alt="Image 1">
    </body></html>""",
            PageData(
                url=BASE_URL,
                heading="",
                first_paragraph="This is the first paragraph.",
                outgoing_links=[f"{BASE_URL}/link1"],
                image_urls=[f"{BASE_URL}/image1.jpg"],
            ),
            id="no_heading",
        ),
        pytest.param(
            """<html><body>
        <h1>Test Title</h1>
        <a href="/link1">Link 1</a>
        <img src="/image1.jpg" alt="Image 1">
    </body></html>""",
            PageData(
                url=BASE_URL,
                heading="Test Title",
                first_paragraph="",
                outgoing_links=[f"{BASE_URL}/link1"],
                image_urls=[f"{BASE_URL}/image1.jpg"],
            ),
            id="no_paragraph",
        ),
        pytest.param(
            """<html><body>
        <h1>Test Title</h1>
        <p>This is the first paragraph.</p>
    </body></html>""",
            PageData(
                url=BASE_URL,
                heading="Test Title",
                first_paragraph="This is the first paragraph.",
                outgoing_links=[],
                image_urls=[],
            ),
            id="no_links_or_images",
        ),
        pytest.param(
            "",
            PageData(
                url=BASE_URL,
                heading="",
                first_paragraph="",
                outgoing_links=[],
                image_urls=[],
            ),
            id="empty_html",
        ),
        pytest.param(
            """<html><body>
        <h1>Test Title</h1>
        <main></main>
        <p>This is the first paragraph.</p>
    </body></html>""",
            PageData(
                url=BASE_URL,
                heading="Test Title",
                first_paragraph="This is the first paragraph.",
                outgoing_links=[],
                image_urls=[],
            ),
            id="no_main_paragraph",
        ),
        pytest.param(
            """<html><body>
        <h1>Test Title</h1>
        <p>This is the first paragraph.</p>
        <a href="/link1">Link 1</a>
        <a href="/link2">Link 2</a>
        <img src="/image1.jpg" alt="Image 1">
        <img src="/image2.jpg" alt="Image 2">
    </body></html>""",
            PageData(
                url=BASE_URL,
                heading="Test Title",
                first_paragraph="This is the first paragraph.",
                outgoing_links=[f"{BASE_URL}/link1", f"{BASE_URL}/link2"],
                image_urls=[f"{BASE_URL}/image1.jpg", f"{BASE_URL}/image2.jpg"],
            ),
            id="multiple_links_and_images",
        ),
        pytest.param(
            """<html><body>
        <h1>Test Title</h1>
        <main>
            <p>This is the first paragraph.</p>
            <a href="/link1">Link 1</a>
            <img src="/image1.jpg" alt="Image 1">
        </main>
    </body></html>""",
            PageData(
                url=BASE_URL,
                heading="Test Title",
                first_paragraph="This is the first paragraph.",
                outgoing_links=[f"{BASE_URL}/link1"],
                image_urls=[f"{BASE_URL}/image1.jpg"],
            ),
            id="nested_in_main",
        ),
    ],
)
def test_extract_page_data(html: str, expected: PageData) -> None:
    """Extracts all fields correctly across various page structures."""
    assert extract_page_data(html, BASE_URL) == expected
