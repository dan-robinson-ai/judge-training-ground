"""Metrics calculation utilities for judge evaluation."""

from app.schemas import EvaluationResult, TestCase


def calculate_cohen_kappa(
    results: list[EvaluationResult],
    test_cases: list[TestCase],
) -> float:
    """
    Calculate Cohen's Kappa between judge verdicts and expected verdicts.

    Cohen's Kappa measures inter-rater agreement accounting for chance:
    κ = (p_o - p_e) / (1 - p_e)

    Where:
    - p_o = observed agreement (accuracy)
    - p_e = expected agreement by chance

    Interpretation:
    - 0.0-0.20: Slight agreement
    - 0.21-0.40: Fair agreement
    - 0.41-0.60: Moderate agreement
    - 0.61-0.80: Substantial agreement
    - 0.81-1.00: Almost perfect agreement

    Args:
        results: List of evaluation results from the judge
        test_cases: List of test cases with expected verdicts

    Returns:
        Cohen's Kappa score (-1 to 1, typically 0 to 1)
    """
    # Build lookup for test cases
    tc_lookup = {tc.id: tc for tc in test_cases}

    # Filter out ERROR results and match with test cases
    valid_pairs = []
    for result in results:
        if result.actual_verdict == "ERROR":
            continue
        tc = tc_lookup.get(result.test_case_id)
        if tc:
            valid_pairs.append((result.actual_verdict, tc.expected_verdict))

    if not valid_pairs:
        return 0.0

    n = len(valid_pairs)

    # Count confusion matrix elements
    # actual_pass_expected_pass, actual_pass_expected_fail, etc.
    pp = sum(1 for a, e in valid_pairs if a == "PASS" and e == "PASS")
    pf = sum(1 for a, e in valid_pairs if a == "PASS" and e == "FAIL")
    fp = sum(1 for a, e in valid_pairs if a == "FAIL" and e == "PASS")
    ff = sum(1 for a, e in valid_pairs if a == "FAIL" and e == "FAIL")

    # Observed agreement (accuracy)
    p_o = (pp + ff) / n

    # Marginal frequencies
    actual_pass = pp + pf
    actual_fail = fp + ff
    expected_pass = pp + fp
    expected_fail = pf + ff

    # Expected agreement by chance
    # p_e = P(actual=PASS) * P(expected=PASS) + P(actual=FAIL) * P(expected=FAIL)
    p_e = (actual_pass * expected_pass + actual_fail * expected_fail) / (n * n)

    # Cohen's Kappa
    if p_e == 1.0:
        # Perfect expected agreement (degenerate case)
        return 1.0 if p_o == 1.0 else 0.0

    kappa = (p_o - p_e) / (1 - p_e)

    return kappa
