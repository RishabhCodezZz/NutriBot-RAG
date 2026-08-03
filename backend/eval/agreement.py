"""Human-vs-judge agreement on faithfulness. A judge score nobody has
validated against a human is decoration; this is what makes it citable.

Usage (from backend/):
    python -m eval.agreement results/run_<ts>/answers.json --out results/run_<ts>/human_labels.json -n 20
    python -m eval.agreement results/run_<ts>/answers.json --report-only --labels results/run_<ts>/human_labels.json
"""
import argparse
import json
from pathlib import Path


def cohens_kappa(labels_a: list, labels_b: list) -> float:
    assert len(labels_a) == len(labels_b) and len(labels_a) > 0
    n = len(labels_a)
    categories = sorted(set(labels_a) | set(labels_b))
    po = sum(1 for a, b in zip(labels_a, labels_b) if a == b) / n
    pe = 0.0
    for c in categories:
        pa = sum(1 for a in labels_a if a == c) / n
        pb = sum(1 for b in labels_b if b == c) / n
        pe += pa * pb
    if pe == 1.0:
        return 1.0
    return (po - pe) / (1 - pe)


def label_session(answers_path: str, out_path: str, n: int):
    with open(answers_path, encoding="utf-8") as f:
        answers = json.load(f)
    sample = [a for a in answers if a.get("faithfulness") is not None][:n]
    if not sample:
        print("No answers with a faithfulness score to label.")
        return

    labels = []
    for item in sample:
        print("=" * 80)
        print("Q:", item["question"])
        print("CONTEXT:", (item.get("context_text") or "")[:500])
        print("ANSWER:", item["answer"])
        print(f"Judge grounded ratio: {item['faithfulness']:.2f}")
        while True:
            raw = input("Your call - is every food claim grounded in context? (1=yes, 0=no): ").strip()
            if raw in ("0", "1"):
                labels.append(int(raw))
                break

    result = [
        {"id": item["id"], "human_label": lab, "judge_faithfulness": item["faithfulness"]}
        for item, lab in zip(sample, labels)
    ]
    Path(out_path).write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(f"Saved {len(result)} human labels to {out_path}")


def compute_kappa_from_labels(labels_path: str):
    with open(labels_path, encoding="utf-8") as f:
        labels = json.load(f)
    human = [entry["human_label"] for entry in labels]
    # Binarize the judge's continuous grounded-ratio at 0.5 to compare against
    # the human's binary yes/no call.
    judge = [1 if entry["judge_faithfulness"] >= 0.5 else 0 for entry in labels]
    kappa = cohens_kappa(human, judge)
    print(f"Cohen's kappa (n={len(labels)}): {kappa:.3f}")
    return kappa, len(labels)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("answers_path")
    parser.add_argument("--out", default="human_labels.json")
    parser.add_argument("-n", type=int, default=20)
    parser.add_argument("--report-only", action="store_true")
    parser.add_argument("--labels", default=None)
    args = parser.parse_args()

    if args.report_only:
        compute_kappa_from_labels(args.labels or args.out)
    else:
        label_session(args.answers_path, args.out, args.n)
        compute_kappa_from_labels(args.out)
