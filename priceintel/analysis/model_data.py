"""The rows the price models are allowed to see.

Module Leader, 26/10/2026, point 4: "Secret's reference data must not enter model training, tuning or
performance evaluation." Rather than rely on remembering that in each notebook, every model matrix is
built by this one function, which reads **only** scraped competitor observations:

* `source_type = 'scrape'` - reference offers live in a different table altogether and own-system
  rows no longer exist;
* `shops.is_own_shop = 0` - Secret is excluded even if it ever gains a listing;
* `scrape_runs.purpose` filters development data out of assessed results.

`group_key` is the listing id: grouped cross-validation keeps every observation of one listing in the
same fold, so a model cannot be scored on a listing it was trained on (point 4, repeated-listing
leakage). `operator_group` is the grouping for the leave-one-operator-group-out check.

`tests/test_no_reference_in_models.py` imports reference offers, then asserts they cannot appear here.
"""
MODEL_COLUMNS = ("observation_id", "group_key", "operator_group", "category", "observed_at",
                 "price_uzs", "is_from_price", "availability", "title")


def model_rows(conn, *, rules_version: str | None = None, purpose: str = "assessed",
               categories: list[str] | None = None) -> list[dict]:
    """Feature rows for the baseline, ridge and tree models. Competitor scrapes only."""
    sql = f"""
        SELECT o.observation_id,
               l.listing_id      AS group_key,
               s.operator_group,
               c.category,
               o.observed_at,
               o.price_uzs,
               o.is_from_price,
               o.availability,
               o.title
        FROM price_observations o
        JOIN listings    l ON l.listing_id = o.listing_id
        JOIN shops       s ON s.shop_id    = l.shop_id
        JOIN scrape_runs r ON r.run_id     = o.run_id
        LEFT JOIN listing_categories c
               ON c.listing_id = l.listing_id AND c.rules_version = ?
        WHERE o.source_type = 'scrape'      -- never reference or own-system rows
          AND s.is_own_shop = 0             -- never Secret
          AND r.purpose = ?
    """
    params: list = [rules_version, purpose]
    if categories:
        sql += f" AND c.category IN ({', '.join('?' * len(categories))})"
        params += categories
    rows = [dict(r) for r in conn.execute(sql + " ORDER BY o.observation_id", params)]
    assert all(tuple(r) == MODEL_COLUMNS for r in rows), "model matrix columns changed"
    return rows
