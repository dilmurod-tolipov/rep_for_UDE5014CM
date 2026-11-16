"""What predicts a listing's price: a baseline and two comparative models.

Analytical question 3, and the Module Leader's clarification 4: *"Retain the category-median baseline
and the previously specified ridge and tree models using competitor data only. Preserve the
validation controls against repeated-listing leakage. Secret's reference data must not enter model
training, tuning or performance evaluation."*

* **Baseline** - predict the median price of the product's category, fitted on the training fold
  only. A baseline that is allowed to see the whole dataset flatters every model compared with it.
* **Ridge regression** - linear, with L2 regularisation because the one-hot operator and category
  columns are collinear by construction (a product has exactly one of each).
* **Decision tree** - captures the interaction a linear model cannot: the same category is priced
  differently by different shops, and a stated stem count means something different in each.

**Leakage control.** Every row comes from `model_data.model_rows`, which reads scraped competitor
observations only. The folds come from `dataset_splits`, written once by the pipeline: grouped folds
keep **all observations of one listing in the same fold**, so a model cannot be scored on a product
it was trained on. Preprocessing - the category medians, the one-hot vocabulary, the scaler - is
fitted on the training fold inside each iteration, never on the whole dataset.

**Tuning is separated from evaluation.** The ridge penalty and the tree depth are chosen by an inner
split *inside the training fold*, so the validation fold is used once, to report. Hyperparameters
chosen this way are recorded with the run.

**Metrics.** MAE in UZS, which is the owner's unit, and the median absolute percentage error, which
is comparable across categories whose prices differ by an order of magnitude. Both are reported
overall and by category, because an average over a catalogue that runs from 18,000 to 15,000,000 UZS
hides more than it shows.

The honest possibility is that the baseline wins: the plan says to evaluate whether either model
improves on it and explain the result, not to find a winner.
"""
import json
from dataclasses import dataclass, field

import numpy as np
from sklearn.linear_model import Ridge
from sklearn.preprocessing import StandardScaler
from sklearn.tree import DecisionTreeRegressor

from priceintel.db import transaction

RIDGE_ALPHAS = (0.1, 1.0, 10.0, 100.0)
TREE_DEPTHS = (2, 3, 4, 6, 8)
RANDOM_SEED = 20261109
POOLED = -1   # the fold value for a metric computed over all folds together


@dataclass
class ModelResult:
    model_name: str
    split_kind: str
    hyperparameters: dict
    n_train: int
    n_validation: int
    metrics: list[tuple[str, str, float, int | None]] = field(default_factory=list)
    notes: str = ""


def load_rows(conn, pipeline_run_id: int) -> list[dict]:
    """One row per included product, with its fold assignments. Competitor data only - the view the
    pipeline writes already excludes Secret, per-stem prices and uncategorised products."""
    return [dict(r) for r in conn.execute("""
        SELECT p.listing_id, p.category, p.operator_group, p.regular_price_uzs AS price,
               p.stem_count, p.n_observations, p.price_changes, p.days_on_sale,
               p.is_outlier, f.price_unit, f.size_cm
        FROM analysis_products p
        LEFT JOIN listing_features f ON f.listing_id = p.listing_id
        WHERE p.pipeline_run_id = ? AND p.included = 1
        ORDER BY p.listing_id""", (pipeline_run_id,))]


def design_matrix(rows: list[dict], categories: list[str], groups: list[str]) -> np.ndarray:
    """One-hot category and operator group, plus the numeric features a listing states about itself.

    The vocabulary is passed in rather than inferred, so the validation fold is encoded with the
    training fold's columns: a category seen only in validation becomes all-zeros instead of
    silently shifting every column."""
    matrix = []
    for r in rows:
        row = [1.0 if r["category"] == c else 0.0 for c in categories]
        row += [1.0 if r["operator_group"] == g else 0.0 for g in groups]
        row += [
            float(r["stem_count"] or 0),
            1.0 if r["stem_count"] else 0.0,           # "the shop stated a stem count"
            float(r["size_cm"] or 0),
            1.0 if r["price_unit"] == "per_bundle" else 0.0,
            float(r["n_observations"] or 1),
            float(r["price_changes"] or 0),
            float(r["days_on_sale"] or 0),
        ]
        matrix.append(row)
    return np.array(matrix, dtype=float)


def metrics_for(actual: np.ndarray, predicted: np.ndarray) -> tuple[float, float]:
    """(MAE in UZS, median absolute percentage error)."""
    mae = float(np.mean(np.abs(actual - predicted)))
    mdape = float(np.median(np.abs((actual - predicted) / actual) * 100.0))
    return mae, mdape


def _category_median_baseline(train: list[dict], validation: list[dict]) -> np.ndarray:
    """Fitted on the training fold only: the median of each category, and the overall median for a
    category the training fold never saw."""
    by_category: dict[str, list[float]] = {}
    for r in train:
        by_category.setdefault(r["category"], []).append(float(r["price"]))
    overall = float(np.median([float(r["price"]) for r in train]))
    medians = {c: float(np.median(v)) for c, v in by_category.items()}
    return np.array([medians.get(r["category"], overall) for r in validation], dtype=float)


def _tune_ridge(x_train, y_train, seed: int) -> float:
    """Choose the penalty on an inner split of the training fold, so the validation fold is used
    once, for reporting."""
    rng = np.random.default_rng(seed)
    index = rng.permutation(len(y_train))
    cut = max(int(len(index) * 0.75), 1)
    inner_train, inner_validation = index[:cut], index[cut:]
    if len(inner_validation) == 0:
        return 1.0
    best, best_error = 1.0, float("inf")
    for alpha in RIDGE_ALPHAS:
        model = Ridge(alpha=alpha).fit(x_train[inner_train], y_train[inner_train])
        error = float(np.mean(np.abs(model.predict(x_train[inner_validation])
                                     - y_train[inner_validation])))
        if error < best_error:
            best, best_error = alpha, error
    return best


def _tune_tree(x_train, y_train, seed: int) -> int:
    rng = np.random.default_rng(seed)
    index = rng.permutation(len(y_train))
    cut = max(int(len(index) * 0.75), 1)
    inner_train, inner_validation = index[:cut], index[cut:]
    if len(inner_validation) == 0:
        return 3
    best, best_error = 3, float("inf")
    for depth in TREE_DEPTHS:
        model = DecisionTreeRegressor(max_depth=depth, random_state=seed).fit(
            x_train[inner_train], y_train[inner_train])
        error = float(np.mean(np.abs(model.predict(x_train[inner_validation])
                                     - y_train[inner_validation])))
        if error < best_error:
            best, best_error = depth, error
    return best


def evaluate(conn, pipeline_run_id: int, *, split_kind: str = "grouped_cv",
             seed: int = RANDOM_SEED) -> list[ModelResult]:
    """Train and score the three models over the folds the pipeline wrote."""
    rows = {r["listing_id"]: r for r in load_rows(conn, pipeline_run_id)}
    folds = conn.execute(
        "SELECT fold, listing_id, part FROM dataset_splits WHERE pipeline_run_id = ?"
        " AND split_kind = ? ORDER BY fold, listing_id", (pipeline_run_id, split_kind)).fetchall()
    by_fold: dict[int, dict[str, list[int]]] = {}
    for f in folds:
        if f["listing_id"] in rows:
            by_fold.setdefault(f["fold"], {"train": [], "validation": [], "test": []})
            by_fold[f["fold"]][f["part"]].append(f["listing_id"])

    results = {name: ModelResult(name, split_kind, {}, 0, 0)
               for name in ("category_median_baseline", "ridge", "decision_tree")}
    pooled: dict[str, list[tuple[np.ndarray, np.ndarray, list[str]]]] = {k: [] for k in results}

    for fold, parts in sorted(by_fold.items()):
        held_out = parts["validation"] or parts["test"]
        train = [rows[i] for i in parts["train"] if i in rows]
        validation = [rows[i] for i in held_out if i in rows]
        if len(train) < 10 or len(validation) < 3:
            continue
        assert not (set(parts["train"]) & set(held_out)), "a listing is in train and validation"

        categories = sorted({r["category"] for r in train})
        groups = sorted({r["operator_group"] for r in train})
        x_train = design_matrix(train, categories, groups)
        x_validation = design_matrix(validation, categories, groups)
        y_train = np.array([float(r["price"]) for r in train])
        y_validation = np.array([float(r["price"]) for r in validation])
        scaler = StandardScaler().fit(x_train)          # fitted on the training fold only
        x_train_s, x_validation_s = scaler.transform(x_train), scaler.transform(x_validation)

        predictions = {
            "category_median_baseline": _category_median_baseline(train, validation),
        }
        alpha = _tune_ridge(x_train_s, y_train, seed + fold)
        predictions["ridge"] = Ridge(alpha=alpha).fit(x_train_s, y_train).predict(x_validation_s)
        depth = _tune_tree(x_train, y_train, seed + fold)
        predictions["decision_tree"] = DecisionTreeRegressor(
            max_depth=depth, random_state=seed).fit(x_train, y_train).predict(x_validation)

        for name, predicted in predictions.items():
            result = results[name]
            result.n_train += len(train)
            result.n_validation += len(validation)
            if name == "ridge":
                result.hyperparameters[f"alpha_fold_{fold}"] = alpha
            if name == "decision_tree":
                result.hyperparameters[f"max_depth_fold_{fold}"] = depth
            mae, mdape = metrics_for(y_validation, predicted)
            result.metrics.append(("all", "mae_uzs", mae, fold))
            result.metrics.append(("all", "mdape_pct", mdape, fold))
            pooled[name].append((y_validation, predicted, [r["category"] for r in validation]))

    for name, folds_data in pooled.items():
        if not folds_data:
            continue
        actual = np.concatenate([a for a, _, _ in folds_data])
        predicted = np.concatenate([p for _, p, _ in folds_data])
        categories = [c for _, _, cs in folds_data for c in cs]
        mae, mdape = metrics_for(actual, predicted)
        results[name].metrics.append(("all", "mae_uzs", mae, POOLED))
        results[name].metrics.append(("all", "mdape_pct", mdape, POOLED))
        for category in sorted(set(categories)):
            mask = np.array([c == category for c in categories])
            if mask.sum() >= 3:
                c_mae, c_mdape = metrics_for(actual[mask], predicted[mask])
                results[name].metrics.append((category, "mae_uzs", c_mae, POOLED))
                results[name].metrics.append((category, "mdape_pct", c_mdape, POOLED))
    return [r for r in results.values() if r.metrics]


def store(conn, pipeline_run_id: int, results: list[ModelResult]) -> int:
    with transaction(conn):
        old = [r[0] for r in conn.execute(
            "SELECT model_run_id FROM model_runs WHERE pipeline_run_id = ?", (pipeline_run_id,))]
        if old:
            conn.executemany("DELETE FROM model_metrics WHERE model_run_id = ?",
                             [(i,) for i in old])
            conn.execute("DELETE FROM model_runs WHERE pipeline_run_id = ?", (pipeline_run_id,))
        for r in results:
            model_run_id = conn.execute(
                "INSERT INTO model_runs (pipeline_run_id, model_name, split_kind, hyperparameters,"
                " n_train, n_validation, notes) VALUES (?, ?, ?, ?, ?, ?, ?) RETURNING model_run_id",
                (pipeline_run_id, r.model_name, r.split_kind, json.dumps(r.hyperparameters),
                 r.n_train, r.n_validation, r.notes)).fetchone()[0]
            conn.executemany(
                "INSERT INTO model_metrics (model_run_id, scope, metric, value, fold)"
                " VALUES (?, ?, ?, ?, ?)",
                [(model_run_id, scope, metric, value, fold)
                 for scope, metric, value, fold in r.metrics])
    return len(results)


def comparison_table(conn, pipeline_run_id: int) -> list[dict]:
    """Each model against the baseline, pooled over folds: the answer to question 3."""
    return [dict(r) for r in conn.execute("""
        SELECT r.model_name, r.split_kind, m.scope, m.metric, m.value
        FROM model_runs r JOIN model_metrics m ON m.model_run_id = r.model_run_id
        WHERE r.pipeline_run_id = ? AND m.fold = -1
        ORDER BY m.scope, m.metric, r.model_name""", (pipeline_run_id,))]
