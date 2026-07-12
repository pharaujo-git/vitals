"""Approximate name matching for duplicate detection.

Kept dependency-free and transparent: bounded Damerau–Levenshtein distance
(adjacent transpositions count as one edit, so swapped letters — the most
common keying error — stay within the threshold).
"""


def damerau_levenshtein(a: str, b: str, cap: int = 3) -> int:
    """Edit distance with adjacent transpositions; short-circuits at `cap`."""
    a, b = a.lower(), b.lower()
    if a == b:
        return 0
    if abs(len(a) - len(b)) > cap:
        return cap
    previous2: list[int] = []
    previous = list(range(len(b) + 1))
    for i, char_a in enumerate(a, start=1):
        current = [i]
        for j, char_b in enumerate(b, start=1):
            cost = 0 if char_a == char_b else 1
            value = min(
                previous[j] + 1,        # deletion
                current[j - 1] + 1,     # insertion
                previous[j - 1] + cost, # substitution
            )
            if i > 1 and j > 1 and char_a == b[j - 2] and a[i - 2] == char_b:
                value = min(value, previous2[j - 2] + 1)  # transposition
            current.append(value)
        if min(current) >= cap:
            return cap
        previous2, previous = previous, current
    return min(previous[len(b)], cap)


def names_similar(a: str, b: str, max_distance: int = 2) -> bool:
    """True for near-identical names; very short names must match exactly."""
    a, b = a.strip().lower(), b.strip().lower()
    if a == b:
        return True
    if min(len(a), len(b)) < 4:
        return False
    return damerau_levenshtein(a, b, cap=max_distance + 1) <= max_distance


def full_name_similar(
    first_a: str, last_a: str, first_b: str, last_b: str, max_total: int = 2
) -> bool:
    """Each component near-identical (short components exact), and the whole
    name within a shared edit budget."""
    if not names_similar(first_a, first_b) or not names_similar(last_a, last_b):
        return False
    total = damerau_levenshtein(first_a.strip().lower(), first_b.strip().lower()) + \
        damerau_levenshtein(last_a.strip().lower(), last_b.strip().lower())
    return total <= max_total
