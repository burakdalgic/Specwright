"""Example: Function with full test coverage matching @requires_tests requirements.

Demonstrates how @requires_tests declares the test cases a function needs,
and how test functions follow the naming convention so the pytest plugin
can verify coverage.
"""

from specwright import requires_tests, spec


@requires_tests(
    happy_path=True,
    edge_cases=["empty_list", "single_item", "already_sorted"],
    error_cases=["non_numeric", "mixed_types"],
)
@spec
def sort_scores(scores: list[int]) -> list[int]:
    """Sort a list of integer scores in ascending order."""
    return sorted(scores)


# --- Matching tests (would live in tests/ in a real project) ---

if __name__ == "__main__":
    # Show the required test names
    reqs = sort_scores.__test_requirements__
    print("Required test functions:")
    for name in reqs.expected_test_names:
        print(f"  {name}")

    # Demonstrate the function works
    print(f"\nsort_scores([3, 1, 2]) = {sort_scores([3, 1, 2])}")
    print(f"sort_scores([])        = {sort_scores([])}")
    print(f"sort_scores([42])      = {sort_scores([42])}")
