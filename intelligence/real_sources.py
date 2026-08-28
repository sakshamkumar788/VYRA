"""
Standard-library RSS/Atom source adapter for VYRA intelligence.

This is intentionally provider-independent.
A real source adapter should only normalize raw feed data into
IntelligenceStory objects. Personal relevance and scoring happen later
in the intelligence scoring layer.
"""

from __future__ import annotations

from datetime import datetime
from email.utils import parsedate_to_datetime
import urllib.request
import xml.etree.ElementTree as ET

from intelligence.models import IntelligenceStory
from intelligence.sources import IntelligenceSource


class RSSIntelligenceSource(IntelligenceSource):
    """
    Fetches RSS/Atom feeds and converts entries into IntelligenceStory.

    This adapter deliberately does not calculate personal relevance.
    It only extracts available feed data.
    """

    def __init__(
        self,
        feed_url: str,
        source_name: str,
        category: str,
        source_trust: int,
        timeout: int = 10,
        max_items: int = 10,
    ) -> None:
        self.feed_url = feed_url
        self.source_name = source_name
        self.category = category
        self.source_trust = source_trust
        self.timeout = timeout
        self.max_items = max_items

    # ------------------------------------------------------------------
    # Public interface
    # ------------------------------------------------------------------

    def fetch(self) -> list[IntelligenceStory]:
        """Fetch and normalize the configured feed."""

        try:
            xml_data = self._download_feed()

        except Exception as e:
            print(f"RSSIntelligenceSource warning: download failed for {self.feed_url}: {e}")
            return []

        try:
            root = ET.fromstring(xml_data)

        except ET.ParseError as e:
            print(f"RSSIntelligenceSource warning: XML parse failed for {self.feed_url}: {e}")
            return []

        stories: list[IntelligenceStory] = []

        for item in self._find_entries(root)[: self.max_items]:
            try:
                story = self._parse_entry(item)

            except Exception as e:
                # Do not let one malformed item break the whole feed.
                print(f"RSSIntelligenceSource warning: failed to parse entry: {e}")
                continue

            if story is not None:
                stories.append(story)

        return stories

    # ------------------------------------------------------------------
    # Feed fetching
    # ------------------------------------------------------------------

    def _download_feed(self) -> bytes:
        """Download the feed as bytes using urllib."""

        request = urllib.request.Request(
            self.feed_url,
            headers={
                "User-Agent": "VYRA-Intelligence/0.1"
            },
        )

        with urllib.request.urlopen(
            request,
            timeout=self.timeout,
        ) as response:
            return response.read()

    # ------------------------------------------------------------------
    # XML helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _local_name(tag: str) -> str:
        """Strip XML namespace information from a tag name."""

        if tag.startswith("{"):
            return tag.rsplit("}", 1)[-1]

        return tag

    def _find_entries(self, root: ET.Element) -> list[ET.Element]:
        """Return all RSS <item> or Atom <entry> elements."""

        entries: list[ET.Element] = []

        for element in root.iter():
            local_name = self._local_name(element.tag)

            if local_name in {"item", "entry"}:
                entries.append(element)

        return entries

    def _find_child(
        self,
        parent: ET.Element,
        child_name: str,
    ) -> ET.Element | None:
        """Find the first direct child with a given local name."""

        for child in parent:
            if self._local_name(child.tag) == child_name:
                return child

        return None

    def _child_text(
        self,
        parent: ET.Element,
        child_name: str,
    ) -> str | None:
        """Return stripped text content for a direct child."""

        child = self._find_child(parent, child_name)

        if child is None:
            return None

        text = child.text or ""
        return text.strip()

    # ------------------------------------------------------------------
    # Entry parsing
    # ------------------------------------------------------------------

    def _parse_entry(
        self,
        entry: ET.Element,
    ) -> IntelligenceStory | None:
        """Convert one RSS/Atom entry into an IntelligenceStory."""

        title = self._child_text(entry, "title")
        summary = (
            self._child_text(entry, "description")
            or self._child_text(entry, "summary")
            or self._child_text(entry, "content")
            or ""
        )

        # A story without a title is not useful.
        if not title:
            return None

        url = self._extract_url(entry)
        published_at = self._extract_published_at(entry)

        return IntelligenceStory(
            title=title.strip(),
            summary=summary.strip(),
            source=self.source_name,
            url=url,
            category=self.category,
            published_at=published_at,
            source_trust=self.source_trust,
        )

    def _extract_url(
        self,
        entry: ET.Element,
    ) -> str | None:
        """Extract a URL from RSS <link> or Atom <link href=...>."""

        link = self._find_child(entry, "link")

        if link is None:
            return None

        # Atom style: <link href="https://..." />
        href = link.attrib.get("href")
        if href:
            return href.strip()

        # RSS style: <link>https://...</link>
        text = link.text or ""
        text = text.strip()

        if text:
            return text

        return None

    def _extract_published_at(
        self,
        entry: ET.Element,
    ) -> datetime | None:
        """Extract publication time from common RSS/Atom fields."""

        raw_date = (
            self._child_text(entry, "pubDate")
            or self._child_text(entry, "published")
            or self._child_text(entry, "updated")
        )

        if not raw_date:
            return None

        return self._parse_date(raw_date)

    @staticmethod
    def _parse_date(raw_date: str) -> datetime | None:
        """Parse common RSS/Atom date formats."""

        raw_date = raw_date.strip()

        if not raw_date:
            return None

        # RSS pubDate is usually RFC 822.
        try:
            return parsedate_to_datetime(raw_date)

        except (TypeError, ValueError):
            pass

        # Atom dates are usually ISO 8601.
        try:
            normalized = raw_date

            if normalized.endswith("Z"):
                normalized = normalized[:-1] + "+00:00"

            return datetime.fromisoformat(normalized)

        except ValueError:
            return None


# ----------------------------------------------------------------------
# Local self-test / demo
# ----------------------------------------------------------------------

if __name__ == "__main__":
    import http.server
    import threading

    from intelligence.models import SourceTrust, StoryCategory

    RSS_XML = b"""<?xml version="1.0"?>
    <rss version="2.0">
      <channel>
        <title>VYRA Test Feed</title>
        <item>
          <title>AI research breakthrough</title>
          <description>A new model improves reasoning.</description>
          <link>https://example.com/ai-story</link>
          <pubDate>Mon, 24 Aug 2026 10:00:00 GMT</pubDate>
        </item>
        <item>
          <description>This entry has no title and must not appear.</description>
          <link>https://example.com/no-title</link>
        </item>
      </channel>
    </rss>
    """

    class _Handler(http.server.BaseHTTPRequestHandler):
        def do_GET(self) -> None:
            self.send_response(200)
            self.send_header(
                "Content-Type",
                "application/rss+xml",
            )
            self.end_headers()
            self.wfile.write(RSS_XML)

        def log_message(self, *args) -> None:
            pass

    server = http.server.HTTPServer(
        ("127.0.0.1", 0),
        _Handler,
    )

    thread = threading.Thread(
        target=server.serve_forever,
        daemon=True,
    )
    thread.start()

    feed_url = (
        f"http://127.0.0.1:{server.server_port}/feed"
    )

    try:
        source = RSSIntelligenceSource(
            feed_url=feed_url,
            source_name="VYRA Local Test",
            category=StoryCategory.AI,
            source_trust=SourceTrust.REPUTABLE,
        )

        stories = source.fetch()

        print("Stories fetched:", len(stories))
        print()

        for story in stories:
            print("Title:", story.title)
            print("Summary:", story.summary)
            print("URL:", story.url)
            print("Category:", story.category)
            print("Source trust:", story.source_trust)
            print("Published at:", story.published_at)
            print("-" * 40)

        assert len(stories) == 1
        assert stories[0].title == "AI research breakthrough"
        assert stories[0].source == "VYRA Local Test"
        assert stories[0].category == StoryCategory.AI
        assert stories[0].url == "https://example.com/ai-story"
        assert stories[0].source_trust == SourceTrust.REPUTABLE
        assert stories[0].published_at is not None

        print("All RSSIntelligenceSource tests passed.")

    finally:
        server.shutdown()
        server.server_close()