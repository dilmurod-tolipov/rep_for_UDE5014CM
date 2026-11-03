"""Import Secret's offers from a file the owner exports, into ``reference_offers``.

Two input shapes, one code path after parsing:

* **Telegram Desktop export** (``result.json``, "JSON, no media"): the owner exports their own
  channel and hands over the file. No account, API key or credential is needed to reproduce the
  project - the file is the input.
* **CSV fallback** (``published_at,post_url,price_uzs,title``), if the owner prefers to keep a price
  list by hand.

What the importer does, and why:

* **Minimises what is stored.** Only the post date, the post link, the price, and a short title.
  Contact lines (phone numbers, @handles, links) are stripped by ``clean_caption`` before a title is
  taken, no media is read, and the full caption is not stored.
* **Records provenance.** Each import row keeps the file name, its SHA-256, the export date and the
  consent note. Importing the same file twice is refused by the UNIQUE constraint on the hash;
  re-importing an updated export adds only the posts that are new, because ``post_url`` is unique.
* **Groups reposts across the whole window.** The Module Leader's clarification of 2026-11-03:
  "An identifiable offer should not become a new independent item solely because its price changes or
  14 days pass." Identity is therefore the **normalised title**, checked against every offer already
  imported, with no time limit and no price condition:

  - same title, same price -> ``exact``: plainly the same offer reposted;
  - same title, different price -> ``uncertain``: the same offer at a new price, or a different
    bouquet reusing a caption. It joins the same group, is flagged, and a robustness check re-runs
    the comparison with uncertain groups excluded;
  - no earlier match -> ``unique``.

  A distinct offer is summarised by the **median** of the prices it was posted at, is dated by its
  first publication, and counts once however often it reappears.
* **Classifies with the committed rules**, so a reference offer and a competitor product are put in
  the same category by exactly the same file.

Nothing here writes to ``price_observations``, and ``tests/test_no_reference_in_models.py`` checks
that no reference row can reach a model matrix.
"""
import csv
import hashlib
import json
from dataclasses import dataclass
from pathlib import Path

from priceintel.analysis.categories import Rules, classify, normalise, register_rules
from priceintel.collect.validate import Rejection
from priceintel.db import transaction
from priceintel.secret.extract import clean_caption, extract_price, title_of

# Identity is title-based and has no time limit (ADR-008). A title that differs by more than
# punctuation or case is a different offer; nothing is matched by price alone.
CHANNEL_URL = "https://t.me/secret_flowersuz"


class ImportError_(ValueError):
    """The export file is not in a shape the importer understands."""


@dataclass(frozen=True)
class ParsedOffer:
    post_id: int
    post_url: str
    published_at: str
    title: str
    price_uzs: int
    raw_price_text: str | None


@dataclass
class ImportSummary:
    import_id: int
    rows_read: int = 0
    rows_stored: int = 0
    rows_skipped: int = 0
    skipped: list[str] = None

    def __post_init__(self):
        self.skipped = self.skipped or []


def _text_of(message: dict) -> str:
    """Telegram writes `text` either as a string or as a list of plain and formatted parts."""
    text = message.get("text", "")
    if isinstance(text, str):
        return text
    return "".join(part if isinstance(part, str) else part.get("text", "") for part in text)


def _iso(value: str) -> str:
    """'2026-10-04T08:42:24' (local, as Telegram writes it) -> UTC-shaped ISO text."""
    return value if value.endswith("Z") else f"{value}Z"


def parse_telegram_export(path: Path) -> tuple[list[ParsedOffer], list[str], int]:
    """Offers found in a Telegram Desktop export, plus a reason for every post skipped."""
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    if "messages" not in data:
        raise ImportError_("not a Telegram Desktop export: no 'messages' key")
    channel = (data.get("name") or "").strip()
    offers, skipped, read = [], [], 0
    for message in data["messages"]:
        if message.get("type") != "message":
            continue
        read += 1
        post_id = message.get("id")
        caption = clean_caption(_text_of(message))
        price = extract_price(caption)
        if isinstance(price, Rejection):
            skipped.append(f"post {post_id}: {price.rule}")
            continue
        price_uzs, raw = price
        offers.append(ParsedOffer(
            post_id=post_id,
            post_url=f"{CHANNEL_URL}/{post_id}",
            published_at=_iso(message.get("date", "")),
            title=title_of(caption, post_id),
            price_uzs=price_uzs,
            raw_price_text=raw))
    if not offers and not skipped:
        raise ImportError_(f"no channel posts found in the export of {channel or 'the channel'}")
    return offers, skipped, read


def parse_csv(path: Path) -> tuple[list[ParsedOffer], list[str], int]:
    """Fallback shape: published_at,post_url,price_uzs,title (one row per offer)."""
    offers, skipped, read = [], [], 0
    with Path(path).open(encoding="utf-8-sig", newline="") as fh:
        for row in csv.DictReader(fh):
            read += 1
            try:
                post_url = row["post_url"].strip()
                offers.append(ParsedOffer(
                    post_id=int(post_url.rstrip("/").rsplit("/", 1)[-1]),
                    post_url=post_url,
                    published_at=_iso(row["published_at"].strip()),
                    title=clean_caption(row["title"]).strip()[:200] or f"Offer {read}",
                    price_uzs=int(str(row["price_uzs"]).replace(" ", "").replace(",", "")),
                    raw_price_text=str(row["price_uzs"])))
            except (KeyError, ValueError) as e:
                skipped.append(f"row {read}: {e}")
    if not offers and not skipped:
        raise ImportError_("the CSV has no rows; expected published_at,post_url,price_uzs,title")
    return offers, skipped, read


def _repost_of(conn, offer: ParsedOffer) -> tuple[int | None, str]:
    """(offer_group_id, confidence) for an earlier post of the same offer, searched over the whole
    import rather than a 14-day window. A price change does not create a new offer; it makes the
    match ``uncertain`` so it can be excluded in a robustness check."""
    title = normalise(offer.title).strip()
    for row in conn.execute(
            "SELECT offer_group_id, title, price_uzs FROM reference_offers"
            " ORDER BY published_at ASC, offer_id ASC"):
        if normalise(row["title"]).strip() == title:
            return row["offer_group_id"], ("exact" if row["price_uzs"] == offer.price_uzs
                                           else "uncertain")
    return None, "unique"


def import_offers(conn, path: Path | str, *, exported_at: str, consent_note: str,
                  purpose: str = "dev", rules: Rules | None = None) -> ImportSummary:
    """Import one export file. Safe to re-run with a newer export: only new posts are added."""
    path = Path(path)
    raw = path.read_bytes()
    digest = hashlib.sha256(raw).hexdigest()
    if conn.execute("SELECT 1 FROM reference_imports WHERE file_sha256 = ?", (digest,)).fetchone():
        raise ImportError_(f"this exact file has already been imported (sha256 {digest[:12]}...)")

    parse = parse_csv if path.suffix.lower() == ".csv" else parse_telegram_export
    offers, skipped, rows_read = parse(path)
    if rules is not None:
        register_rules(conn, rules)

    with transaction(conn):
        import_id = conn.execute(
            "INSERT INTO reference_imports (source_kind, file_name, file_sha256, exported_at,"
            " purpose, consent_note) VALUES (?, ?, ?, ?, ?, ?)",
            ("csv" if parse is parse_csv else "telegram_export", path.name, digest, exported_at,
             purpose, consent_note)).lastrowid
        summary = ImportSummary(import_id, rows_read=rows_read, skipped=list(skipped))
        for offer in sorted(offers, key=lambda o: o.published_at):
            if conn.execute("SELECT 1 FROM reference_offers WHERE post_url = ?",
                            (offer.post_url,)).fetchone():
                summary.skipped.append(f"post {offer.post_id}: already imported")
                continue
            category = rules_version = None
            if rules is not None:
                category = classify(offer.title, None, None, rules).category
                rules_version = rules.version
            group, confidence = _repost_of(conn, offer)
            offer_id = conn.execute(
                "INSERT INTO reference_offers (import_id, post_id, post_url, published_at, title,"
                " price_uzs, raw_price_text, offer_group_id, category, rules_version,"
                " match_confidence) VALUES (?, ?, ?, ?, ?, ?, ?, COALESCE(?, 0), ?, ?, ?)"
                " RETURNING offer_id",
                (import_id, offer.post_id, offer.post_url, offer.published_at, offer.title,
                 offer.price_uzs, offer.raw_price_text, group, category, rules_version,
                 confidence)).fetchone()[0]
            if group is None:   # first post of its group: the group is the offer itself
                conn.execute("UPDATE reference_offers SET offer_group_id = ? WHERE offer_id = ?",
                             (offer_id, offer_id))
            if confidence == "uncertain":
                summary.skipped.append(
                    f"post {offer.post_id}: same caption as an earlier offer at a different price "
                    f"({offer.price_uzs:,} UZS) - grouped, flagged uncertain")
            summary.rows_stored += 1
        summary.rows_skipped = len(summary.skipped)
        conn.execute("UPDATE reference_imports SET rows_read = ?, rows_stored = ?, rows_skipped = ?"
                     " WHERE import_id = ?",
                     (summary.rows_read, summary.rows_stored, summary.rows_skipped, import_id))
    return summary


def distinct_offers_by_category(conn, *, since: str | None = None, until: str | None = None):
    """Distinct offers (reposts collapsed) per category - Table 2 of the sampling plan."""
    sql = ("SELECT category, COUNT(*) AS n_offers FROM v_reference_distinct_offers"
           " WHERE 1 = 1")
    params: list = []
    if since:
        sql += " AND first_published_at >= ?"
        params.append(since)
    if until:
        sql += " AND first_published_at <= ?"
        params.append(until)
    return [dict(r) for r in conn.execute(sql + " GROUP BY category ORDER BY n_offers DESC", params)]
