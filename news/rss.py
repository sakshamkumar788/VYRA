from urllib.request import Request, urlopen
from xml.etree import ElementTree

from news.base import NewsProvider
from news.models import NewsItem


class RSSNewsProvider(NewsProvider):
    """
    Generic RSS news provider.

    The feed URL is configurable so VYRA is not tied to
    a particular news provider.
    """

    def __init__(
        self,
        feed_url: str,
        source_name: str = "RSS",
    ) -> None:
        self.feed_url = feed_url
        self.source_name = source_name

    def get_latest(
        self,
        limit: int = 5,
    ) -> list[NewsItem]:
        """Fetch and parse RSS items."""

        request = Request(
            self.feed_url,
            headers={
                "User-Agent": "VYRA/1.0",
            },
        )

        with urlopen(
            request,
            timeout=10,
        ) as response:
            data = response.read()

        root = ElementTree.fromstring(data)

        items: list[NewsItem] = []

        for item in root.findall(".//item"):
            title_element = item.find("title")
            description_element = item.find("description")
            link_element = item.find("link")

            title = (
                title_element.text.strip()
                if title_element is not None
                and title_element.text
                else ""
            )

            if not title:
                continue

            summary = (
                description_element.text.strip()
                if description_element is not None
                and description_element.text
                else None
            )

            url = (
                link_element.text.strip()
                if link_element is not None
                and link_element.text
                else None
            )

            items.append(
                NewsItem(
                    title=title,
                    summary=summary,
                    source=self.source_name,
                    url=url,
                )
            )

            if len(items) >= limit:
                break

        return items