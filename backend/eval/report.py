"""Aggregation and report writing. Nothing here calls Gemini - it only
turns the per-case result dicts produced by run.py into results.csv,
answers.json, and a human-readable report.md. Nothing from the original
evaluate.py was persisted anywhere; that's the gap this closes.
"""
import csv
import json
import statistics
from pathlib import Path


def _mean(values):
    clean = [v for v in values if v is not None]
    return sum(clean) / len(clean) if clean else None


def _stdev(values):
    clean = [v for v in values if v is not None]
    return statistics.pstdev(clean) if len(clean) > 1 else 0.0 if clean else None


def _rate(values):
    clean = [v for v in values if v is not None]
    return sum(1 for v in clean if v) / len(clean) if clean else None


NUMERIC_FIELDS = [
    "recall@5", "recall@10", "precision", "hit_rate", "mrr", "ndcg@10",
    "hallucination_rate", "numeric_accuracy", "keyword_coverage",
    "faithfulness", "relevance",
]
RATE_FIELDS = ["safety_violation", "disclaimer_present", "decline_detected", "injection_resisted"]


def aggregate(results: list) -> dict:
    agg = {"n": len(results)}
    for field in NUMERIC_FIELDS:
        values = [r.get(field) for r in results]
        agg[field] = _mean(values)
        agg[f"{field}_std"] = _stdev(values)
    for field in RATE_FIELDS:
        agg[f"{field}_rate"] = _rate([r.get(field) for r in results])
    return agg


def aggregate_by_category(results: list) -> dict:
    categories = sorted({r["category"] for r in results})
    return {cat: aggregate([r for r in results if r["category"] == cat]) for cat in categories}


def write_csv(path: Path, results: list):
    if not results:
        return
    fieldnames = [
        "id", "category", "lang", "variant", "recall@5", "recall@10", "precision",
        "hit_rate", "mrr", "ndcg@10", "hallucination_rate", "numeric_accuracy",
        "keyword_coverage", "safety_violation", "faithfulness", "relevance",
        "disclaimer_present", "decline_detected", "injection_resisted",
    ]
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        for r in results:
            writer.writerow(r)


def write_json(path: Path, results: list):
    path.write_text(json.dumps(results, indent=2, default=str), encoding="utf-8")


def _fmt(x, pct=False):
    if x is None:
        return "n/a"
    if pct:
        return f"{x * 100:.1f}%"
    return f"{x:.3f}"


def write_markdown(path: Path, results_by_variant: dict, kappa: float = None, kappa_n: int = 0):
    lines = ["# NutriBot Evaluation Report", ""]

    lines.append("## Ablation table")
    lines.append("")
    lines.append("| Variant | n | Recall@5 | Hallucination rate | Relevance (1-5) | Safety violation rate |")
    lines.append("|---|---|---|---|---|---|")
    for variant, results in results_by_variant.items():
        agg = aggregate(results)
        lines.append(
            f"| {variant} | {agg['n']} | {_fmt(agg['recall@5'])} | "
            f"{_fmt(agg['hallucination_rate'], pct=True)} | {_fmt(agg['relevance'])} | "
            f"{_fmt(agg['safety_violation_rate'], pct=True)} |"
        )
    lines.append("")

    primary = "dense_rerank_hardened" if "dense_rerank_hardened" in results_by_variant else next(iter(results_by_variant))
    primary_results = results_by_variant[primary]
    agg = aggregate(primary_results)

    lines.append(f"## Full metrics - primary variant (`{primary}`)")
    lines.append("")
    lines.append("| Metric | Mean | Std |")
    lines.append("|---|---|---|")
    for field in NUMERIC_FIELDS:
        lines.append(f"| {field} | {_fmt(agg[field])} | {_fmt(agg[f'{field}_std'])} |")
    for field in RATE_FIELDS:
        lines.append(f"| {field}_rate | {_fmt(agg[f'{field}_rate'], pct=True)} | - |")
    lines.append("")

    lines.append("## Per-category breakdown (primary variant)")
    lines.append("")
    lines.append("| Category | n | Recall@5 | Hallucination rate | Relevance | Safety violation rate |")
    lines.append("|---|---|---|---|---|---|")
    for cat, cat_agg in aggregate_by_category(primary_results).items():
        lines.append(
            f"| {cat} | {cat_agg['n']} | {_fmt(cat_agg['recall@5'])} | "
            f"{_fmt(cat_agg['hallucination_rate'], pct=True)} | {_fmt(cat_agg['relevance'])} | "
            f"{_fmt(cat_agg['safety_violation_rate'], pct=True)} |"
        )
    lines.append("")

    lines.append("## Judge agreement")
    lines.append("")
    if kappa is not None:
        lines.append(f"Cohen's kappa (human vs. judge faithfulness, n={kappa_n}): **{kappa:.3f}**")
    else:
        lines.append(
            "Not computed for this run. Run `python -m eval.agreement <answers.json path> "
            "--out human_labels.json` to hand-label a sample and get kappa against the judge."
        )
    lines.append("")

    lines.append("## Worst-scoring cases (primary variant)")
    lines.append("")
    scored = [r for r in primary_results if r.get("hallucination_rate") is not None]
    scored.sort(key=lambda r: r["hallucination_rate"], reverse=True)
    for r in scored[:5]:
        lines.append(f"- `{r['id']}` ({r['category']}): hallucination_rate={_fmt(r['hallucination_rate'], pct=True)}, "
                      f"hallucinated_foods={r.get('hallucinated_foods')}")
    violations = [r for r in primary_results if r.get("safety_violation")]
    if violations:
        lines.append("")
        lines.append("### Safety violations")
        for r in violations:
            lines.append(f"- `{r['id']}` ({r['category']}): forbidden foods mentioned = {r.get('forbidden_hit')}")

    path.write_text("\n".join(lines), encoding="utf-8")
