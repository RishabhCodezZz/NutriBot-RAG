from eval.metrics import retrieval


GOLD = ["food_56", "food_49"]
RETRIEVED = ["food_1", "food_56", "food_49", "food_3"]


def test_recall_at_k():
    assert retrieval.recall_at_k(GOLD, RETRIEVED, 5) == 1.0
    assert retrieval.recall_at_k(GOLD, RETRIEVED[:1], 5) == 0.0


def test_recall_at_k_none_when_gold_empty():
    assert retrieval.recall_at_k([], RETRIEVED, 5) is None


def test_precision_at_k():
    assert retrieval.precision_at_k(GOLD, RETRIEVED, 4) == 0.5


def test_hit_rate_at_k():
    assert retrieval.hit_rate_at_k(GOLD, RETRIEVED, 4) == 1.0
    assert retrieval.hit_rate_at_k(GOLD, ["food_1", "food_3"], 4) == 0.0


def test_mrr_finds_first_relevant_rank():
    assert retrieval.mrr(GOLD, RETRIEVED) == 0.5  # food_56 is at rank 2
    assert retrieval.mrr(GOLD, ["food_56", "food_1"]) == 1.0
    assert retrieval.mrr(GOLD, ["food_1", "food_3"]) == 0.0


def test_ndcg_perfect_order_scores_higher_than_reversed():
    perfect = retrieval.ndcg_at_k(GOLD, ["food_56", "food_49", "food_1"], 10)
    reversed_order = retrieval.ndcg_at_k(GOLD, ["food_1", "food_49", "food_56"], 10)
    assert perfect > reversed_order
    assert perfect == 1.0
