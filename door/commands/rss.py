import datetime

import requests
import feedparser
from loguru import logger as log
from pydantic import BaseModel, HttpUrl

from .base_command import BaseCommand


class Feed(BaseModel):
    name: str
    short_name: str
    url: HttpUrl
    last_updated: datetime.datetime | None = None
    headlines: list[str] | None = None


FEEDS = [
    Feed(name="The Onion", short_name="onion", url="https://theonion.com/rss"),
    Feed(
        name="Wikinews",
        short_name="wiki",
        url="https://en.wikinews.org/w/index.php?title=Special:NewsFeed&feed=rss&categories=Published&notcategories=No%20publish%7CArchived%7cAutoArchived%7cdisputed&namespace=0&count=15&ordermethod=categoryadd&stablepages=only",
    ),
    Feed(name="Hackaday", short_name="hack", url="https://hackaday.com/feed/"),
    Feed(name="2600.com", short_name="2600", url="http://www.2600.com/rss.xml"),
    Feed(name="Yahoo News", short_name="yahoo", url="https://www.yahoo.com/news/rss"),
]


def get_feed_titles(feed: Feed) -> list[str]:
    response = requests.get(feed.url)
    if response.status_code != 200:
        log.warning(f"Bad response from feed '{feed.short_name}")
        return
    parsed = feedparser.parse(response.text)
    if "entries" not in parsed:
        log.warning(f"No entries in feed response for '{feed.short_name}")
        return

    return [p["title"] for p in parsed["entries"]]


class RSS(BaseCommand):
    command = "rss"
    description = "returns headlines from RSS feeds"
    help = "Show feeds with 'rss list'."

    def load(self):
        # TODO read from configuration, feeds shouldn't be hard-coded
        self.feed_names = [f.short_name for f in FEEDS]

    def invoke(self, msg: str, node: str) -> str:
        self.run_in_thread(self.fetch, msg, node)

    def fetch(self, msg: str, node: str):
        # strip invocation command
        msg = msg[len(self.command) :].lower().lstrip().rstrip()

        # return a list
        if msg[:4] == "list":
            return self.send_dm(self.list_feeds(), node)

        # search for the requested feed
        feed: Feed
        found_feed: Feed = None
        for feed in FEEDS:
            if feed.short_name in msg:
                found_feed = feed
                break

        if found_feed:
            titles = get_feed_titles(feed)
            reply = self.build_reply(titles)
        else:
            reply = f"Feed not found. {self.list_feeds()}"

        self.send_dm(reply, node)

    def list_feeds(self) -> str:
        feed: Feed
        return "Installed RSS feeds:\n\n" + "\n".join(
            [f"{feed.short_name}: {feed.name}" for feed in FEEDS]
        )

    def build_reply(self, titles: list[str]) -> str:
        reply = ""
        for t in titles:
            proposed = f"{t}\n\n"
            if len(reply + proposed) > 200:
                break
            else:
                reply += proposed
        return reply.strip()
