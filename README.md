# youtube-links

youtube-links adds a Sphinx directive that creates styled YouTube video links with
automatic title extraction.

## Basic usage

To add a YouTube link to your document, use the `youtube` directive with the desired
YouTube URL:

```
.. youtube:: https://www.youtube.com/watch?v=dQw4w9WgXcQ
```

You can also specify a custom title:

```
.. youtube:: https://www.youtube.com/watch?v=dQw4w9WgXcQ
   :title: Custom Video Title
```

## Project setup

youtube-links is published on PyPI and can be installed with:

```bash
pip install youtube-links
```

After adding youtube-links to your Python project, update your Sphinx's conf.py file to
include youtube-links as one of its extensions:

```python
extensions = [
    "youtube_links"
]
```

## Community and support

You can report any issues or bugs on the project's [GitHub
repository](https://github.com/canonical/youtube-links).

youtube-links is covered by the [Ubuntu Code of
Conduct](https://ubuntu.com/community/ethos/code-of-conduct).

## License and copyright

youtube-links is released under the [GPL-3.0 license](LICENSE).

© 2025 Canonical Ltd.
