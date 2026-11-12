"""Turn collected observations into the analysis dataset, recording every decision.

One command rebuilds everything the analysis reads::

    python -m priceintel pipeline --purpose assessed

The stages are the ones the brief names, in order, and each is a function below:

1. **Ingestion and schema checking** - the database has already refused anything of the wrong type or
   outside its range (STRICT tables, CHECK constraints, triggers), and the validator has quarantined
   what it could not parse. The pipeline therefore starts from records that are known to be
   well-formed, and counts what it reads so that the numbers in the report add up.
2. **Cleaning.** The decisions, and why each one is defensible:

   * *Invalid records* never reach here: they are in ``rejected_records`` with the rule that refused
     them, and they are counted in the quality checks.
   * *Starting prices* ("от 550 000") are **not used as prices**, because they are not the price of
     one identified product. They are not thrown away either: loveflowers.uz publishes a starting
     price on 230 of its 354 cards, so dropping those products silently would remove most of the
     largest competitor without the reader seeing it. A product whose observations are all starting
     prices is stored with ``exclusion_reason = 'starting_price_only'`` and its lower-bound price, so
     the count is visible and the approved sensitivity check can switch it back on. Where a product
     has both kinds, only the real prices are summarised.
   * *Duplicates* cannot exist: ``UNIQUE (listing_id, run_id)`` makes a re-run idempotent, and one
     product is one listing by ``UNIQUE (shop_id, url)``. The pipeline asserts this rather than
     assuming it.
   * *Missing values* are never imputed. A product with no category is excluded and counted; a
     missing stem count stays NULL; a missing availability stays unknown. Guessing any of them would
     invent evidence.
   * *Per-stem prices* are excluded from the assortment comparison and counted: 18,000 UZS for one
     gerbera is not comparable with a bouquet, and pooling them would drag a category median down.
   * *Outliers* are **flagged, not removed**. Removing them silently would be a decision the reader
     cannot see; the flag lets the robustness check re-run the comparison without them, which is what
     the approved plan promises. The rule is the median absolute deviation within a category **and
     one operator group**: MAD does not assume a normal distribution and is not moved by the outliers
     it is detecting, and a product is only unusual compared with its own shop's assortment - judged
     against all four groups at once, every one of pro-buket's 19 rose bouquets was flagged, simply
     because another shop in that category sells roses by the stem.
3. **Transformation.** Each product is summarised once: the median of its regular prices over the
   window. A product observed 56 times contributes exactly as much as one observed once, which is
   what the Module Leader asked for in clarification 4.
4. **Integration.** Category, price unit, stem count and operator group are joined onto each product,
   so the analysis reads one table instead of re-deriving joins.
5. **Feature engineering and splits.** Grouped folds keep every observation of a listing together,
   leave-one-operator-group-out gives the sensitivity check its folds, and a chronological split
   holds out the last part of the window. The splits are written once per build, so an evaluation
   cannot quietly reshuffle them.

Nothing here reads Secret's reference offers: the comparison joins them later, and no model ever
sees them (``model_data.py``).
"""
import hashlib
import statistics
from collections import Counter, defaultdict
from dataclasses import dataclass, field

from priceintel.db import transaction
from priceintel.gitinfo import git_state

PIPELINE_VERSION = "1.0.0"
OUTLIER_MAD_MULTIPLIER = 8.0      # how many MADs from the category median counts as an outlier
MIN_FOR_OUTLIER_RULE = 8          # below this, a category is too small to judge an outlier
CV_FOLDS = 5
CHRONOLOGICAL_TEST_FRACTION = 0.25


@dataclass
class StageCounts:
    observations_in: int = 0
    observations_from_price: int = 0
    observations_used: int = 0
    products_in: int = 0
    products_no_category: int = 0
    products_per_stem: int = 0
    products_starting_price_only: int = 0
    products_outliers_flagged: int = 0
    products_included: int = 0


@dataclass
class Product:
    listing_id: int
    operator_group: str
    category: str | None
    price_unit: str | None
    stem_count: int | None
    regular_prices: list[int] = field(default_factory=list)
    sale_prices: list[int] = field(default_factory=list)
    starting_prices: list[int] = field(default_factory=list)
    days: set = field(default_factory=set)
    first_observed_at: str = ""
    last_observed_at: str = ""
    price_changes: int = 0
    days_on_sale: int = 0
    availability_last: str | None = None

    @property
    def regular_price(self) -> int | None:
        """The median regular price, or - when the shop only ever advertised a starting price - that
        starting price, which is a lower bound and is marked as one by the exclusion reason."""
        if self.regular_prices:
            return round(statistics.median(self.regular_prices))
        return round(statistics.median(self.starting_prices)) if self.starting_prices else None

    @property
    def only_starting_prices(self) -> bool:
        return not self.regular_prices and bool(self.starting_prices)

    @property
    def n_observations(self) -> int:
        """Every time the product was seen, whether or not the figure could be used as a price."""
        return len(self.regular_prices) + len(self.starting_prices)

    @property
    def sale_price(self) -> int | None:
        return round(statistics.median(self.sale_prices)) if self.sale_prices else None


def _read_observations(conn, purpose: str, window_start: str, window_end: str,
                       rules_version: str) -> tuple[dict[int, Product], StageCounts]:
    """Stages 1-2: read well-formed observations in the window and apply the cleaning rules."""
    counts = StageCounts()
    rows = conn.execute("""
        SELECT l.listing_id, s.operator_group, c.category, f.price_unit, f.stem_count,
               o.observed_at, o.price_uzs, o.old_price_uzs, o.is_from_price, o.availability
        FROM price_observations o
        JOIN listings    l ON l.listing_id = o.listing_id
        JOIN shops       s ON s.shop_id    = l.shop_id
        JOIN scrape_runs r ON r.run_id     = o.run_id
        LEFT JOIN listing_categories c ON c.listing_id = l.listing_id
                                      AND c.rules_version = :rules_version
        LEFT JOIN listing_features   f ON f.listing_id = l.listing_id
                                      AND f.rules_version = :rules_version
        WHERE o.source_type = 'scrape'          -- primary data only; never a reference offer
          AND s.is_own_shop = 0
          AND r.purpose = :purpose
          AND substr(o.observed_at, 1, 10) BETWEEN :window_start AND :window_end
        ORDER BY l.listing_id, o.observed_at, o.observation_id
    """, {"rules_version": rules_version, "purpose": purpose,
          "window_start": window_start, "window_end": window_end}).fetchall()

    products: dict[int, Product] = {}
    previous_price: dict[int, int] = {}
    for r in rows:
        counts.observations_in += 1
        p = products.get(r["listing_id"])
        if p is None:
            p = products[r["listing_id"]] = Product(
                r["listing_id"], r["operator_group"], r["category"], r["price_unit"],
                r["stem_count"], first_observed_at=r["observed_at"])
        if r["is_from_price"]:
            # Kept as a lower bound, never summarised as a price (see the module docstring).
            counts.observations_from_price += 1
            p.starting_prices.append(r["price_uzs"])
            p.days.add(r["observed_at"][:10])
            p.last_observed_at = r["observed_at"]
            p.availability_last = r["availability"]
            continue
        counts.observations_used += 1
        # The regular price is the old price when the shop shows a sale, else the current price.
        p.regular_prices.append(r["old_price_uzs"] or r["price_uzs"])
        p.sale_prices.append(r["price_uzs"])
        p.days.add(r["observed_at"][:10])
        p.last_observed_at = r["observed_at"]
        p.availability_last = r["availability"]
        if r["old_price_uzs"]:
            p.days_on_sale += 1
        if r["listing_id"] in previous_price and previous_price[r["listing_id"]] != r["price_uzs"]:
            p.price_changes += 1
        previous_price[r["listing_id"]] = r["price_uzs"]

    counts.products_in = len(products)
    return products, counts


def _flag_outliers(products: dict[int, Product]) -> set[int]:
    """Products whose regular price is far from its category's median, by median absolute deviation.

    MAD is used rather than a standard deviation because the distributions are skewed and a few
    extreme prices would inflate an SD enough to hide themselves. Flagged, never dropped."""
    by_category: dict[tuple, list[Product]] = defaultdict(list)
    for p in products.values():
        if p.category and p.regular_price is not None and not p.only_starting_prices:
            by_category[(p.category, p.operator_group)].append(p)

    outliers: set[int] = set()
    for group in by_category.values():
        prices = [p.regular_price for p in group]
        if len(prices) < MIN_FOR_OUTLIER_RULE:
            continue    # too few products in this shop's category to say what is unusual for it
        median = statistics.median(prices)
        mad = statistics.median([abs(price - median) for price in prices]) or 1
        for p in group:
            if abs(p.regular_price - median) > OUTLIER_MAD_MULTIPLIER * mad:
                outliers.add(p.listing_id)
    return outliers


def _exclusion_reason(p: Product) -> str | None:
    """Why a product is not used in the assortment comparison. None means it is used."""
    if p.category is None or p.category in ("unclassified", "out_of_scope"):
        return "no_analysis_category"
    if p.price_unit == "per_stem":
        return "priced_per_stem"
    if p.only_starting_prices:
        return "starting_price_only"
    if p.regular_price is None:
        return "no_regular_price"
    return None


def _folds(listing_ids: list[int], n_folds: int, seed: str) -> dict[int, int]:
    """Deterministic fold per listing: the same build always gives the same folds, and every
    observation of a listing is in exactly one fold (leakage control for grouped CV)."""
    return {listing_id: int(hashlib.sha256(f"{seed}:{listing_id}".encode()).hexdigest(), 16) % n_folds
            for listing_id in listing_ids}


def _write_splits(conn, pipeline_run_id: int, products: dict[int, Product],
                  included: list[int]) -> None:
    rows = []
    folds = _folds(included, CV_FOLDS, seed=str(pipeline_run_id))
    for listing_id, fold in folds.items():
        for f in range(CV_FOLDS):
            rows.append((pipeline_run_id, listing_id, "grouped_cv", f,
                         "validation" if f == fold else "train"))

    # Leave-one-operator-group-out: one fold per group, that group held out.
    groups = sorted({products[i].operator_group for i in included})
    for f, group in enumerate(groups):
        for listing_id in included:
            rows.append((pipeline_run_id, listing_id, "leave_one_group_out", f,
                         "validation" if products[listing_id].operator_group == group else "train"))

    # Chronological: the products first seen in the last quarter of the window are the test set.
    ordered = sorted(included, key=lambda i: products[i].first_observed_at)
    cut = int(len(ordered) * (1 - CHRONOLOGICAL_TEST_FRACTION))
    for position, listing_id in enumerate(ordered):
        rows.append((pipeline_run_id, listing_id, "chronological", 0,
                     "train" if position < cut else "test"))

    conn.executemany("INSERT INTO dataset_splits (pipeline_run_id, listing_id, split_kind, fold,"
                     " part) VALUES (?, ?, ?, ?, ?)", rows)


def build_dataset(conn, *, purpose: str, window_start: str, window_end: str,
                  rules_version: str) -> tuple[int, StageCounts]:
    """Run the whole pipeline and store the dataset. Returns (pipeline_run_id, stage counts)."""
    products, counts = _read_observations(conn, purpose, window_start, window_end, rules_version)
    if not products:
        raise ValueError(f"no {purpose} observations between {window_start} and {window_end}")

    # The database guarantees one observation per (listing, run); assert it rather than assume it.
    duplicates = conn.execute("SELECT COUNT(*) FROM (SELECT listing_id, run_id"
                              " FROM price_observations GROUP BY listing_id, run_id"
                              " HAVING COUNT(*) > 1)").fetchone()[0]
    if duplicates:
        raise ValueError(f"{duplicates} duplicate (listing, run) pairs: the dataset would be wrong")

    outliers = _flag_outliers(products)
    counts.products_outliers_flagged = len(outliers)
    commit, dirty = git_state()

    with transaction(conn):
        pipeline_run_id = conn.execute(
            "INSERT INTO pipeline_runs (pipeline_version, purpose, window_start, window_end,"
            " rules_version, git_commit, git_dirty) VALUES (?, ?, ?, ?, ?, ?, ?) RETURNING"
            " pipeline_run_id",
            (PIPELINE_VERSION, purpose, window_start, window_end, rules_version, commit,
             int(dirty))).fetchone()[0]

        included: list[int] = []
        reasons: Counter = Counter()
        for p in products.values():
            reason = _exclusion_reason(p)
            if reason:
                reasons[reason] += 1
            else:
                included.append(p.listing_id)
            conn.execute(
                "INSERT INTO analysis_products (pipeline_run_id, listing_id, operator_group,"
                " category, price_unit, stem_count, regular_price_uzs, sale_price_uzs,"
                " n_observations, observed_days, first_observed_at, last_observed_at,"
                " price_changes, days_on_sale, availability_last, is_outlier, included,"
                " exclusion_reason) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (pipeline_run_id, p.listing_id, p.operator_group, p.category, p.price_unit,
                 p.stem_count, p.regular_price, p.sale_price, p.n_observations, len(p.days),
                 p.first_observed_at, p.last_observed_at, p.price_changes, p.days_on_sale,
                 p.availability_last, int(p.listing_id in outliers), int(reason is None), reason))

        counts.products_no_category = reasons["no_analysis_category"]
        counts.products_per_stem = reasons["priced_per_stem"]
        counts.products_starting_price_only = reasons["starting_price_only"]
        counts.products_included = len(included)
        # "no_regular_price" cannot happen while the validator requires a price, but if it ever does
        # the row must still be accounted for, so it is folded into the category count rather than
        # left to break the stage arithmetic.
        counts.products_no_category += reasons["no_regular_price"]

        _write_splits(conn, pipeline_run_id, products, included)
        conn.execute(
            "UPDATE pipeline_runs SET observations_in = ?, observations_from_price = ?,"
            " observations_used = ?, products_in = ?, products_no_category = ?,"
            " products_per_stem = ?, products_starting_price_only = ?,"
            " products_outliers_flagged = ?, products_included = ? WHERE pipeline_run_id = ?",
            (counts.observations_in, counts.observations_from_price, counts.observations_used,
             counts.products_in, counts.products_no_category, counts.products_per_stem,
             counts.products_starting_price_only, counts.products_outliers_flagged,
             counts.products_included, pipeline_run_id))
    return pipeline_run_id, counts


def dataset_summary(conn, pipeline_run_id: int) -> list[dict]:
    """Included products per category and operator group, with their median price."""
    return [dict(r) for r in conn.execute("""
        SELECT category, operator_group,
               COUNT(*)                                  AS n_products,
               SUM(is_outlier)                           AS outliers,
               CAST(AVG(regular_price_uzs) AS INTEGER)   AS mean_price_uzs,
               MIN(regular_price_uzs)                    AS min_price_uzs,
               MAX(regular_price_uzs)                    AS max_price_uzs
        FROM analysis_products
        WHERE pipeline_run_id = ? AND included = 1
        GROUP BY category, operator_group
        ORDER BY category, operator_group""", (pipeline_run_id,))]
