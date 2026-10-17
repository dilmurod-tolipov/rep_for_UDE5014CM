"""Parse the public web preview of a Telegram channel (https://t.me/s/<channel>).

Layout (2026-10-17):
  <div class="tgme_widget_message ..." data-post="secret_flowersuz/19040">
     <div class="tgme_widget_message_text ...">caption with <br/> line breaks</div>
     <a class="tgme_widget_message_date" ...><time datetime="2026-10-17T17:40:19+00:00"></a>
  <link rel="prev" href="/s/secret_flowersuz?before=19013">   <- older posts
"""
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from urllib.parse import urljoin

from bs4 import BeautifulSoup


@dataclass(frozen=True)
class ChannelPost:
    post_url: str      # https://t.me/<channel>/<id>
    post_id: int
    published_at: str  # UTC, YYYY-MM-DDTHH:MM:SSZ
    text: str          # caption, line breaks kept


def to_utc(iso: str) -> str:
    return datetime.fromisoformat(iso).astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def parse_channel_page(html: str, page_url: str) -> tuple[list[ChannelPost], str | None]:
    """Returns the posts on the page (oldest first, as Telegram shows them) and the URL of older posts."""
    soup = BeautifulSoup(html, "html.parser")
    posts = []
    for msg in soup.select("div.tgme_widget_message[data-post]"):
        ref = msg["data-post"]
        m = re.fullmatch(r"([A-Za-z0-9_]+)/(\d+)", ref)
        time_el = msg.select_one(".tgme_widget_message_date time[datetime]")
        if not m or time_el is None:
            continue
        text_el = msg.select_one(".tgme_widget_message_text")
        text = ""
        if text_el is not None:
            for br in text_el.find_all("br"):
                br.replace_with("\n")
            text = text_el.get_text()
        posts.append(ChannelPost(f"https://t.me/{m.group(1)}/{m.group(2)}", int(m.group(2)),
                                 to_utc(time_el["datetime"]), text.strip()))
    prev = soup.select_one('link[rel="prev"][href]')
    return posts, (urljoin(page_url, prev["href"]) if prev else None)
