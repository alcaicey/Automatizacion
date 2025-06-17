import re


def clean_percentage(text: str) -> str:
    """Limpia porcentajes como '(-0,34%)' de un texto."""
    return re.sub(r"\s*\([-+]?\d+(?:[.,]\d+)?%\)", "", text)


__all__ = ["clean_percentage"]