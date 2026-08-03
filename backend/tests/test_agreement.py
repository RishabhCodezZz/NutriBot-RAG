from eval.agreement import cohens_kappa


def test_perfect_agreement_gives_kappa_one():
    assert cohens_kappa([1, 0, 1, 0, 1], [1, 0, 1, 0, 1]) == 1.0


def test_no_agreement_beyond_chance_gives_low_kappa():
    # both raters always disagree
    kappa = cohens_kappa([1, 1, 1, 1], [0, 0, 0, 0])
    assert kappa < 0.5


def test_partial_agreement_between_zero_and_one():
    kappa = cohens_kappa([1, 0, 1, 0, 1, 0, 1, 0], [1, 0, 1, 1, 1, 0, 0, 0])
    assert 0.0 < kappa < 1.0
