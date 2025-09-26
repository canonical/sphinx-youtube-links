"""Defines the youtube directive and connects it to Sphinx."""

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

from docutils import nodes
from docutils.parsers.rst import Directive
from docutils.parsers.rst import directives
from youtube_links import common
import requests
from sphinx.application import Sphinx
from sphinx.util.typing import ExtensionMetadata
from bs4 import BeautifulSoup

cache: dict[str, str] = {}


class YouTubeLink(Directive):
    """Define the youtube directive's arguments and behavior."""

    required_arguments = 1
    optional_arguments = 0
    has_content = False
    option_spec = {"title": directives.unchanged}

    def run(self) -> list[nodes.Node]:
        """Generate a raw HTML node containing the formatted link."""
        title: str = ""

        if "title" in self.options:
            title = self.options["title"]
        elif self.arguments[0] in cache:
            title = cache[self.arguments[0]]
        else:
            try:
                r = requests.get(self.arguments[0], timeout=10)
                r.raise_for_status()
                soup = BeautifulSoup(r.text, "html.parser")
                if soup.title:
                    title = soup.title.get_text()
                    cache[self.arguments[0]] = title
            except requests.HTTPError as err:
                print(err)

        fragment: str = f"""
            <p class="youtube_link">
              <a href="{self.arguments[0]}" target="_blank">
                <span title="{title}" class="play_icon">▶</span>
                <span title="{title}">Watch on YouTube</span>
              </a>
            </p>
        """
        raw = nodes.raw(text=fragment, format="html")

        return [raw]


def setup(app: Sphinx) -> ExtensionMetadata:
    """Connect the extension and its assets to Sphinx.

    app (Sphinx): Sphinx application instance.
    """
    app.add_directive("youtube", YouTubeLink)
    common.add_css(app, "youtube.css")

    return {"version": "0.1", "parallel_read_safe": True, "parallel_write_safe": True}
