"""One-off: run the LLM-judge against a run's already-saved answers instead
of regenerating them - the generation (Ollama Cloud) side of a run doesn't
need to be repeated just because the judge (Gemini) side wasn't measured the
first time due to a bad API key. Saves Ollama quota and ~15-20 minutes of
regeneration for exactly the same answers already on disk.

Usage (from backend/): python -m eval.judge_existing_run <run_dir>
"""
import argparse
import json
from pathlib import Path

from eval import ratelimit
from eval.metrics import judge as judge_metrics


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("run_dir")
    parser.add_argument("--rpm", type=int, default=15)
    parser.add_argument("--sleep", type=float, default=1.0)
    args = parser.parse_args()

    ratelimit.configure(args.rpm)
    run_dir = Path(args.run_dir)
    progress_path = run_dir / "progress.jsonl"

    with open(progress_path, encoding="utf-8") as f:
        results = [json.loads(line) for line in f if line.strip()]

    out_path = run_dir / "judge_results.jsonl"
    with open(out_path, "w", encoding="utf-8") as out:
        for i, r in enumerate(results):
            print(f"[{i + 1}/{len(results)}] {r['id']}", flush=True)
            try:
                faithfulness, _ = judge_metrics.judge_faithfulness(r["context_text"], r["answer"])
                relevance, _ = judge_metrics.judge_relevance(r["question"], r["answer"])
                instr = judge_metrics.judge_instruction_following(r["question"], r["context_text"], r["answer"])
            except Exception as e:
                print(f"  [error] {r['id']} failed: {e}", flush=True)
                faithfulness, relevance, instr = None, None, {}
            out.write(json.dumps({
                "id": r["id"], "category": r["category"],
                "faithfulness": faithfulness, "relevance": relevance,
                "instruction_following": instr,
            }) + "\n")
            out.flush()

    print(f"\nDone. Judge results written to {out_path}", flush=True)


if __name__ == "__main__":
    main()
