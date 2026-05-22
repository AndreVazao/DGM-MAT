from difflib import SequenceMatcher


def similarity(
    a: str,
    b: str,
) -> float:

    return SequenceMatcher(
        None,
        a.lower(),
        b.lower(),
    ).ratio()
