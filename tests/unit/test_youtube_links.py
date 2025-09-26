# This file is part of youtube-links.
#
# Copyright 2025 Canonical Ltd.
#
# This program is free software: you can redistribute it and/or modify it under the
# terms of the GNU Lesser General Public License version 3, as published by the Free
# Software Foundation.
#
# This program is distributed in the hope that it will be useful, but WITHOUT ANY
# WARRANTY; without even the implied warranties of MERCHANTABILITY, SATISFACTORY
# QUALITY, or FITNESS FOR A PARTICULAR PURPOSE. See the GNU Lesser General Public
# License for more details.
#
# You should have received a copy of the GNU Lesser General Public License along with
# this program.  If not, see <http://www.gnu.org/licenses/>.

"""Unit tests for youtube-links extension."""

# Ignore import organization warnings
# ruff: noqa: E402
# ruff: noqa: PLC0415

from unittest.mock import Mock, patch

from docutils.parsers.rst import directives
from docutils.statemachine import StringList
from sphinx.application import Sphinx
from youtube_links import YouTubeLink, setup


class TestYouTubeLinksSetup:
    """Test the extension setup function."""

    def test_setup_returns_metadata(self):
        """Test that setup returns proper extension metadata."""
        app_mock = Mock(spec=Sphinx)
        app_mock.add_directive = Mock()

        with patch("youtube_links.common.add_css") as mock_add_css:
            result = setup(app_mock)

        assert result.get("version", "") == "0.1"
        assert result.get("parallel_read_safe", "") is True
        assert result.get("parallel_write_safe", "") is True

        # Verify the directive is registered
        app_mock.add_directive.assert_called_once_with("youtube", YouTubeLink)

        # Verify CSS is added
        mock_add_css.assert_called_once_with(app_mock, "youtube.css")


class TestYouTubeLinkDirective:
    """Test the YouTubeLink directive."""

    def setup_method(self):
        """Set up test fixtures."""
        self.directive = YouTubeLink(
            name="youtube",
            arguments=["https://www.youtube.com/watch?v=dQw4w9WgXcQ"],
            options={},
            content=StringList(),
            lineno=1,
            content_offset=0,
            block_text="",
            state=Mock(),
            state_machine=Mock(),
        )

    def test_directive_options(self):
        """Test that the directive has correct options configured."""
        assert YouTubeLink.required_arguments == 1
        assert YouTubeLink.optional_arguments == 0
        assert YouTubeLink.has_content is False

        directive_spec = YouTubeLink.option_spec if YouTubeLink.option_spec else {}
        assert "title" in directive_spec
        assert directive_spec["title"] == directives.unchanged

    def test_run_with_custom_title(self):
        """Test directive execution with custom title."""
        self.directive.options = {"title": "Custom Video Title"}

        result = self.directive.run()

        assert len(result) == 1
        raw_node = result[0]
        # For raw nodes, the HTML content is stored in the node's children as text
        html_content = str(raw_node.children[0]) if raw_node.children else ""
        assert "Custom Video Title" in html_content
        assert "https://www.youtube.com/watch?v=dQw4w9WgXcQ" in html_content
        assert "youtube_link" in html_content
        assert "Watch on YouTube" in html_content

    @patch("youtube_links.requests.get")
    @patch("youtube_links.BeautifulSoup")
    def test_run_with_automatic_title(self, mock_bs, mock_get):
        """Test directive execution with automatic title extraction."""
        # Mock successful HTTP response
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_response.text = (
            "<html><head><title>Amazing Video - YouTube</title></head></html>"
        )
        mock_get.return_value = mock_response

        # Mock BeautifulSoup
        mock_soup = Mock()
        mock_soup.title.get_text.return_value = "Amazing Video - YouTube"
        mock_bs.return_value = mock_soup

        # Clear the cache to ensure fresh request
        youtube_links.cache.clear()

        result = self.directive.run()

        assert len(result) == 1
        raw_node = result[0]
        html_content = str(raw_node.children[0]) if raw_node.children else ""
        assert "Amazing Video - YouTube" in html_content
        assert "https://www.youtube.com/watch?v=dQw4w9WgXcQ" in html_content

        mock_get.assert_called_once_with(
            "https://www.youtube.com/watch?v=dQw4w9WgXcQ", timeout=10
        )

    @patch("youtube_links.requests.get")
    def test_run_with_http_error(self, mock_get):
        """Test directive execution when HTTP request fails."""
        import requests

        # Mock HTTP error
        mock_get.side_effect = requests.HTTPError("404 Not Found")

        # Clear the cache to ensure fresh request
        youtube_links.cache.clear()

        with patch("builtins.print") as mock_print:
            result = self.directive.run()

        # Should still return a result, but without title from HTTP
        assert len(result) == 1
        raw_node = result[0]
        html_content = str(raw_node.children[0]) if raw_node.children else ""
        assert "https://www.youtube.com/watch?v=dQw4w9WgXcQ" in html_content

        # Should have printed the error
        mock_print.assert_called_once()

    def test_run_uses_cache(self):
        """Test that the directive uses cached titles."""
        # Pre-populate cache
        url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
        youtube_links.cache[url] = "Cached Title"

        result = self.directive.run()

        assert len(result) == 1
        raw_node = result[0]
        html_content = str(raw_node.children[0]) if raw_node.children else ""
        assert "Cached Title" in html_content

    def test_html_output_structure(self):
        """Test that the generated HTML has the correct structure."""
        self.directive.options = {"title": "Test Title"}

        result = self.directive.run()
        raw_node = result[0]
        html_content = str(raw_node.children[0]) if raw_node.children else ""

        # Check for expected HTML structure
        assert 'class="youtube_link"' in html_content
        assert 'target="_blank"' in html_content
        assert 'class="play_icon"' in html_content
        assert "▶" in html_content  # Play icon
        assert "Watch on YouTube" in html_content


# Import the module after defining the tests
import youtube_links
