# For each RSS feed, add two lines to the config.ini file
# to specify the name and URL of the feed as follows:
#
# [door.commands.rss]
# feed.onion.name = The Onion
# feed.onion.url = https://theonion.com/rss

import datetime

import requests
import feedparser
from loguru import logger as log
from pydantic import BaseModel, HttpUrl

from . import BaseCommand
from inspect import getmodule


class Feed(BaseModel):
    name: str
    short_name: str
    url: HttpUrl
    last_updated: datetime.datetime | None = None
    headlines: list[str] | None = None


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
        self.feeds = self.get_feeds()
        self.feed_names = [f.short_name for f in self.feeds]

    # Read feeds from settings
    def get_feeds(self):
        feeds = []
        previous = None
        name = None
        url = None
        for key, value in self.settings.items(getmodule(self).__name__, raw=True):
            item = key.split(".")
            if item[0] == "feed" and len(item) == 3:
                short_name = item[1]
                attr = item[2]
                if previous != short_name:
                    previous = short_name
                    name = None
                    url = None
                if attr == "name":
                    name = value
                if attr == "url":
                    url = value
                if name and url:
                    feeds.append(Feed(name=name, short_name=short_name, url=url))
        return feeds

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
        for feed in self.feeds:
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
            [f"{feed.short_name}: {feed.name}" for feed in self.feeds]
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
