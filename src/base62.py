"""Base62 conversion using the alphabet 0-9, a-z, A-Z."""

ALPHABET = "0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"


def encode(value: int) -> str:
    """Encode a non-negative integer as a base62 string."""
    if not isinstance(value, int) or isinstance(value, bool):
        raise TypeError("value must be an integer")
    if value < 0:
        raise ValueError("value must be non-negative")
    if value == 0:
        return ALPHABET[0]

    digits = []
    while value:
        value, remainder = divmod(value, len(ALPHABET))
        digits.append(ALPHABET[remainder])
    return "".join(reversed(digits))


def decode(code: str) -> int:
    """Decode a non-empty base62 string into a non-negative integer."""
    if not isinstance(code, str):
        raise TypeError("code must be a string")
    if not code:
        raise ValueError("code must not be empty")

    value = 0
    for character in code:
        try:
            digit = ALPHABET.index(character)
        except ValueError as exc:
            raise ValueError(f"invalid base62 character: {character!r}") from exc
        value = value * len(ALPHABET) + digit
    return value
