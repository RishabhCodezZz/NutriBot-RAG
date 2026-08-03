"""Evaluation CLI. Run from backend/:

    python -m eval.run --config current --runs 1
    python -m eval.run --config all --runs 3 --judge-scope primary

--config current   only the production pipeline (dense retrieval + reranker + hardened prompt)
--config all        the full 5-row ablation (see eval/ablation.py)
--judge-scope        primary (default, cheapest) | all | none
--runs N             repeat every case N times and report mean +/- std (default 1)
--limit N            only evaluate the first N test cases (for smoke-testing without burning quota)
--sleep S             seconds to sleep between cases, gentle on free-tier rate limits (default 2.0)

Writes results/run_<timestamp>/{results.csv, answers.json, report.md}.
"""
import argparse
import time
from datetime import datetime
from pathlib import Path

import config
from eval import ablation, report, testset
from eval.metrics import grounding as grounding_metrics
from eval.metrics import judge as judge_metrics
from eval.metrics import retrieval as retrieval_metrics
from eval.metrics import safety as safety_metrics
from eval.translate import translate

PRIMARY_VARIANT = "dense_rerank_hardened"
RESULTS_DIR = Path(__file__).resolve().parent.parent / "eval" / "results"


def resolve_english_query(case):
    if case.lang == "en":
        return case.question
    try:
        text, _ = translate(case.question, to="en")
        return text
    except Exception as e:
        print(f"  [warn] translation failed for {case.id} ({e}); using question_en_reference")
        return case.question_en_reference or case.question


def run_one_case(case, variant: str, run_judge: bool):
    query_en = resolve_english_query(case)
    history_text = testset.history_to_text(case.history, config.HISTORY_MAX_TURNS)

    answer, context_docs, _prompt = ablation.run_variant(variant, query_en, history_text)

    vocab = grounding_metrics.load_vocab()
    mentioned = grounding_metrics.extract_mentioned_foods(answer, vocab)
    hallucination_rate, _, hallucinated = grounding_metrics.hallucinated_food_rate(answer, context_docs, vocab)
    keyword_cov = grounding_metrics.keyword_coverage(answer, case.must_include)
    numeric_acc, _numeric_details = grounding_metrics.numeric_accuracy(answer, vocab)

    retrieved_ids = [d.doc_id for d in context_docs]
    recall5 = retrieval_metrics.recall_at_k(case.gold_doc_ids, retrieved_ids, 5)
    recall10 = retrieval_metrics.recall_at_k(case.gold_doc_ids, retrieved_ids, 10)
    precision = retrieval_metrics.precision_at_k(case.gold_doc_ids, retrieved_ids, max(len(retrieved_ids), 1))
    hit_rate = retrieval_metrics.hit_rate_at_k(case.gold_doc_ids, retrieved_ids, max(len(retrieved_ids), 1))
    mrr_score = retrieval_metrics.mrr(case.gold_doc_ids, retrieved_ids)
    ndcg = retrieval_metrics.ndcg_at_k(case.gold_doc_ids, retrieved_ids, 10)

    forbidden_hit = safety_metrics.allergen_violations(mentioned, case.forbidden_foods)
    context_text = "\n".join(f"- {d.text}" for d in context_docs)

    faithfulness = relevance = None
    instr = {}
    if run_judge:
        faithfulness, _faith_raw = judge_metrics.judge_faithfulness(context_text, answer)
        relevance, _rel_raw = judge_metrics.judge_relevance(case.question, answer)
        instr = judge_metrics.judge_instruction_following(case.question, context_text, answer)

    disclaimer = safety_metrics.disclaimer_present(answer) if case.category == "condition" else None
    decline_detected = safety_metrics.out_of_scope_decline(answer) if case.expect_decline else None
    injection_resisted = safety_metrics.injection_resistance(answer) if case.is_injection else None

    return {
        "id": case.id,
        "category": case.category,
        "lang": case.lang,
        "variant": variant,
        "question": case.question,
        "query_en": query_en,
        "answer": answer,
        "context_text": context_text,
        "retrieved_ids": retrieved_ids,
        "mentioned_foods": sorted(mentioned),
        "hallucinated_foods": sorted(hallucinated),
        "hallucination_rate": hallucination_rate,
        "forbidden_hit": sorted(forbidden_hit),
        "safety_violation": bool(forbidden_hit),
        "keyword_coverage": keyword_cov,
        "numeric_accuracy": numeric_acc,
        "recall@5": recall5,
        "recall@10": recall10,
        "precision": precision,
        "hit_rate": hit_rate,
        "mrr": mrr_score,
        "ndcg@10": ndcg,
        "faithfulness": faithfulness,
        "relevance": relevance,
        "instruction_following": instr,
        "disclaimer_present": disclaimer,
        "decline_detected": decline_detected,
        "injection_resisted": injection_resisted,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", choices=["current", "all"], default="current")
    parser.add_argument("--judge-scope", choices=["primary", "all", "none"], default="primary")
    parser.add_argument("--runs", type=int, default=1)
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--sleep", type=float, default=2.0)
    parser.add_argument("--cases", default=None)
    args = parser.parse_args()

    variants = ablation.VARIANTS if args.config == "all" else [PRIMARY_VARIANT]
    cases = testset.load_test_cases(args.cases)
    if args.limit:
        cases = cases[: args.limit]

    run_dir = RESULTS_DIR / f"run_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    run_dir.mkdir(parents=True, exist_ok=True)

    results_by_variant = {}
    for variant in variants:
        run_judge = args.judge_scope == "all" or (args.judge_scope == "primary" and variant == PRIMARY_VARIANT)
        variant_results = []
        for run_idx in range(args.runs):
            for case in cases:
                print(f"[{variant}] run {run_idx + 1}/{args.runs} - {case.id}")
                try:
                    result = run_one_case(case, variant, run_judge)
                except Exception as e:
                    print(f"  [error] {case.id} failed: {e}")
                    result = {"id": case.id, "category": case.category, "lang": case.lang,
                              "variant": variant, "error": str(e)}
                variant_results.append(result)
                time.sleep(args.sleep)
        results_by_variant[variant] = variant_results

    all_results = [r for results in results_by_variant.values() for r in results]
    report.write_json(run_dir / "answers.json", all_results)
    report.write_csv(run_dir / "results.csv", all_results)
    report.write_markdown(run_dir / "report.md", results_by_variant)

    print(f"\nDone. Report written to {run_dir / 'report.md'}")


if __name__ == "__main__":
    main()
