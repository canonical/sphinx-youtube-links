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

"""Simple integration tests for youtube-links extension."""

# Ignore import organization warnings
# ruff: noqa: E402
# ruff: noqa: PLC0415

import sys
from importlib import import_module
from pathlib import Path
from typing import cast
from unittest.mock import Mock

from docutils import nodes
from docutils.statemachine import StringList

# Add the extension to the path
sys.path.insert(0, str(Path(__file__).parents[2] / "sphinx_youtube_links"))


def test_extension_can_be_imported():
    """Test that the extension can be imported without errors."""
    try:
        sphinx_youtube_links = import_module("sphinx_youtube_links")

        assert hasattr(sphinx_youtube_links, "setup")
        assert callable(sphinx_youtube_links.setup)
        assert hasattr(sphinx_youtube_links, "YouTubeLink")
    except ImportError as e:
        pytest.fail(f"Failed to import sphinx_youtube_links: {e}")


def test_extension_setup_function():
    """Test that the setup function returns correct metadata."""
    from unittest.mock import Mock

    import sphinx_youtube_links

    app_mock = Mock()
    app_mock.add_directive = Mock()

    with patch("sphinx_youtube_links.common.add_css"):
        result = sphinx_youtube_links.setup(app_mock)

    assert "version" in result
    assert "parallel_read_safe" in result
    assert "parallel_write_safe" in result
    assert result["parallel_read_safe"] is True
    assert result["parallel_write_safe"] is True

    # Check that directive was registered
    app_mock.add_directive.assert_called_once_with(
        "youtube", sphinx_youtube_links.YouTubeLink
    )


def test_youtube_directive_instantiation():
    """Test that YouTube directive can be instantiated."""
    from unittest.mock import Mock

    import sphinx_youtube_links

    # Test directive can be created
    directive = sphinx_youtube_links.YouTubeLink(
        name="youtube",
        arguments=["https://www.youtube.com/watch?v=test"],
        options={"title": "Test Title"},
        content=StringList(),
        lineno=1,
        content_offset=0,
        block_text="",
        state=Mock(),
        state_machine=Mock(),
    )

    assert directive.required_arguments == 1
    assert directive.optional_arguments == 0
    assert directive.has_content is False
    directive_spec = directive.option_spec if directive.option_spec else {}
    assert "title" in directive_spec


def test_youtube_directive_execution():
    """Test that YouTube directive can be executed."""
    from unittest.mock import Mock

    import sphinx_youtube_links

    directive = sphinx_youtube_links.YouTubeLink(
        name="youtube",
        arguments=["https://www.youtube.com/watch?v=test"],
        options={"title": "Test Title"},
        content=StringList(),
        lineno=1,
        content_offset=0,
        block_text="",
        state=Mock(),
        state_machine=Mock(),
    )

    result = directive.run()

    assert len(result) == 1
    raw_node = cast(nodes.raw, result[0])
    assert raw_node.tagname == "raw"
    assert raw_node.children

    html_content = str(raw_node.children[0])
    assert "Test Title" in html_content
    assert "https://www.youtube.com/watch?v=test" in html_content
    assert "youtube_link" in html_content


# Import necessary modules
import shutil
import subprocess
from unittest.mock import patch

import bs4
import pytest


@pytest.fixture
def example_project(request) -> Path:
    project_root = request.config.rootpath
    example_dir = project_root / "tests/integration/example"

    target_dir = Path().resolve() / "example"
    shutil.copytree(example_dir, target_dir, dirs_exist_ok=True)

    return target_dir


# Canned response for the video page that the example project links to, so that the
# build doesn't depend on youtube.com being reachable.
FAKE_VIDEO_URL = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
FAKE_VIDEO_TITLE = "Fake video title - YouTube"


def fake_get(url: str, timeout: float) -> Mock:
    assert url == FAKE_VIDEO_URL
    response = Mock()
    response.raise_for_status.return_value = None
    response.text = f"<html><head><title>{FAKE_VIDEO_TITLE}</title></head></html>"
    return response


@pytest.mark.slow
def test_sphinx_build(example_project, mocker):
    """Ensure that Sphinx builds successfully."""
    import sphinx_youtube_links
    from sphinx.cmd.build import build_main

    # Run Sphinx in this process so that the HTTP requests can be patched.
    mocker.patch.dict(sphinx_youtube_links.cache, clear=True)
    mock_get = mocker.patch("sphinx_youtube_links.requests.get", side_effect=fake_get)

    build_dir = example_project / "_build"
    exit_code = build_main(["-b", "html", "-W", str(example_project), str(build_dir)])
    assert exit_code == 0

    # The video with a :title: option isn't fetched, and the cache prevents a
    # second request for the video that appears on two pages.
    mock_get.assert_called_once_with(FAKE_VIDEO_URL, timeout=10)

    index = build_dir / "index.html"

    # Rename the test output to something more meaningful
    shutil.copytree(
        build_dir, build_dir.parents[1] / ".test_output", dirs_exist_ok=True
    )
    soup = bs4.BeautifulSoup(index.read_text(), features="lxml")

    shutil.rmtree(example_project)  # Delete copied source

    titles = [
        span["title"]
        for link in soup.find_all("p", {"class": "youtube_link"})
        for span in link.find_all("span", {"class": "play_icon"})
    ]
    assert titles == [FAKE_VIDEO_TITLE, "Custom Title Video"]
