"""Deterministic retrieval metrics against hand-labelled gold_doc_ids.

Every function returns None when gold_ids is empty - some test cases
(e.g. condition_08, a deliberate stress test with no good answer in the
corpus) have no gold set on purpose, and averaging in a fabricated 0 would
distort the aggregate rather than honestly reporting "not applicable".
"""
import math


def recall_at_k(gold_ids, retrieved_ids, k):
    if not gold_ids:
        return None
    top_k = set(retrieved_ids[:k])
    hits = len(top_k & set(gold_ids))
    return hits / len(gold_ids)


def precision_at_k(gold_ids, retrieved_ids, k):
    if not gold_ids:
        return None
    top_k = retrieved_ids[:k]
    if not top_k:
        return 0.0
    hits = len(set(top_k) & set(gold_ids))
    return hits / len(top_k)


def hit_rate_at_k(gold_ids, retrieved_ids, k):
    if not gold_ids:
        return None
    top_k = set(retrieved_ids[:k])
    return 1.0 if top_k & set(gold_ids) else 0.0


def mrr(gold_ids, retrieved_ids):
    if not gold_ids:
        return None
    gold = set(gold_ids)
    for i, doc_id in enumerate(retrieved_ids, start=1):
        if doc_id in gold:
            return 1.0 / i
    return 0.0


def ndcg_at_k(gold_ids, retrieved_ids, k):
    if not gold_ids:
        return None
    gold = set(gold_ids)
    dcg = 0.0
    for i, doc_id in enumerate(retrieved_ids[:k], start=1):
        rel = 1.0 if doc_id in gold else 0.0
        dcg += rel / math.log2(i + 1)
    ideal_hits = min(len(gold), k)
    idcg = sum(1.0 / math.log2(i + 1) for i in range(1, ideal_hits + 1))
    return dcg / idcg if idcg > 0 else 0.0
