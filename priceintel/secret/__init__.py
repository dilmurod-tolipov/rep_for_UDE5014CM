"""Caption parsing for Secret's own offers.

The collector that read the channel's public web preview was removed on 2026-10-29: Telegram's
Content Licensing and AI Scraping Terms restrict scraping and reuse of platform data, and the
Module Leader (26/10/2026, point 1) accepted an owner-provided export as reference data instead.
What remains is ``extract.py``, which turns one caption into (title, price) and strips contact
lines; it is used by the reference importer (``priceintel/reference/offers.py``).
"""
