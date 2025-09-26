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

from docutils import nodes
from docutils.statemachine import StringList

# Add the extension to the path
sys.path.insert(0, str(Path(__file__).parents[2] / "youtube_links"))


def test_extension_can_be_imported():
    """Test that the extension can be imported without errors."""
    try:
        youtube_links = import_module("youtube_links")

        assert hasattr(youtube_links, "setup")
        assert callable(youtube_links.setup)
        assert hasattr(youtube_links, "YouTubeLink")
    except ImportError as e:
        pytest.fail(f"Failed to import youtube_links: {e}")


def test_extension_setup_function():
    """Test that the setup function returns correct metadata."""
    from unittest.mock import Mock

    import youtube_links

    app_mock = Mock()
    app_mock.add_directive = Mock()

    with patch("youtube_links.common.add_css"):
        result = youtube_links.setup(app_mock)

    assert "version" in result
    assert "parallel_read_safe" in result
    assert "parallel_write_safe" in result
    assert result["parallel_read_safe"] is True
    assert result["parallel_write_safe"] is True

    # Check that directive was registered
    app_mock.add_directive.assert_called_once_with("youtube", youtube_links.YouTubeLink)


def test_youtube_directive_instantiation():
    """Test that YouTube directive can be instantiated."""
    from unittest.mock import Mock

    import youtube_links

    # Test directive can be created
    directive = youtube_links.YouTubeLink(
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

    import youtube_links

    directive = youtube_links.YouTubeLink(
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


@pytest.mark.slow
def test_sphinx_build(example_project):
    """Ensure that Sphinx builds successfully."""
    build_dir = example_project / "_build"
    subprocess.check_call(
        ["sphinx-build", "-b", "html", "-W", example_project, build_dir],
    )

    index = build_dir / "index.html"

    # Rename the test output to something more meaningful
    shutil.copytree(
        build_dir, build_dir.parents[1] / ".test_output", dirs_exist_ok=True
    )
    soup = bs4.BeautifulSoup(index.read_text(), features="lxml")

    shutil.rmtree(example_project)  # Delete copied source

    ext_text = soup.find("p")
    if ext_text:
        print("Successful build.")
    else:
        pytest.fail("Directive output not found in document.")
