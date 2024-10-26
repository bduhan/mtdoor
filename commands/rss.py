import datetime

import requests
import feedparser
from loguru import logger as log
from pydantic import BaseModel, HttpUrl

from .base import BaseCommand, CommandLoadError, CommandRunError


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
        feed: Feed
        # strip invocation command
        msg = msg[len(self.command) :].lower().lstrip().rstrip()
        log.debug(f"[{msg}]")

        # return a list
        if msg[:4] == "list":
            return self.list_feeds()

        for feed in FEEDS:
            if feed.short_name in msg:
                titles = get_feed_titles(feed)
                return self.build_reply(titles)
        return f"Feed not found. Send '{self.command} list' to see a list."

    def list_feeds(self) -> str:
        feed: Feed
        return "Installed RSS feeds:\n\n" + "\n".join(
            [f"{feed.short_name}: {feed.name}" for feed in FEEDS]
        )
    
    def build_reply(self, titles: list[str]) -> str:
        reply = ""
        for t in titles:
            proposed = f"{t}\n\n"
            # print(len(proposed))
            if len(reply + proposed) > 200:
                break
            else:
                reply += proposed
        return reply.strip()
