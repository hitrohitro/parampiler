"""Step 0 normalizer: Victorian Controlled English (VCE) -> SIE++."""

from __future__ import annotations

import re


class NormalizationError(Exception):
    """Raised when Victorian text cannot be normalized safely."""


class Normalizer:
    """Rule-based normalizer from Victorian phrases to SIE++ syntax."""

    def normalize(self, text: str) -> str:
        if not text or not text.strip():
            raise NormalizationError("Input text is empty")

        normalized = text.strip().lower()
        normalized = normalized.replace("\n", " ")

        # Convert sentence punctuation into statement separators.
        # Keep decimal points intact (e.g., 1250.75).
        normalized = re.sub(r";+", ",", normalized)
        normalized = re.sub(r"\.(?=\s*[a-z])", ",", normalized)
        normalized = re.sub(r"(?<!\d)\.(?!\d)|(?<=\D)\.(?=\s|$)", ",", normalized)

        # Remove polite/filler phrases that are semantically neutral.
        normalized = re.sub(r"\bpray\b[:,]?", "", normalized)
        normalized = re.sub(r"\bfinally\b[:,]?", "", normalized)
        normalized = re.sub(r"\band likewise\b[:,]?", ",", normalized)
        normalized = re.sub(r"\bthereafter\b[:,]?", ",", normalized)
        normalized = re.sub(r"\blikewise\b[:,]?", ",", normalized)

        # Block keywords.
        normalized = re.sub(r"\bcommence\b", "begin", normalized)
        normalized = re.sub(r"\bconclude\b", "end", normalized)

        # Condition phrase mapping.
        normalized = re.sub(r"\bbe\s+less\s+than\b", "is less than", normalized)
        normalized = re.sub(r"\bbe\s+greater\s+than\b", "is greater than", normalized)
        normalized = re.sub(r"\bbe\s+equal\s+to\b", "is equal to", normalized)
        normalized = re.sub(r"\bbe\s+not\s+equal\s+to\b", "is not equal to", normalized)

        # Core statement mapping.
        normalized = self._normalize_multi_assign(normalized)

        substitutions = [
            # Assignment/initialization.
            (
                r"\bassign\s+unto\s+variable\s+([a-z_]\w*)\s+the\s+value\s+([^,]+)",
                r"set \1 to \2",
            ),
            (
                r"\bassign\s+unto\s+([a-z_]\w*)\s+the\s+value\s+([^,]+)",
                r"set \1 to \2",
            ),
            (
                r"\bbestow\s+upon\s+([a-z_]\w*)\s+the\s+value\s+([^,]+)",
                r"set \1 to \2",
            ),
            (r"\blet\s+([a-z_]\w*)\s+be\s+([^,]+)", r"set \1 to \2"),
            # Arithmetic rewrites.
            (r"\bincrease\s+([a-z_]\w*)\s+by\s+([^,]+)", r"add \2 to \1"),
            (r"\baugment\s+([a-z_]\w*)\s+by\s+([^,]+)", r"add \2 to \1"),
            (r"\bdecrease\s+([a-z_]\w*)\s+by\s+([^,]+)", r"set \1 to \1 minus \2"),
            (
                r"\badd\s+([a-z_]\w*)\s+and\s+([a-z_]\w*)\s+and\s+place\s+the\s+result\s+into\s+([a-z_]\w*)",
                r"set \3 to \1 plus \2",
            ),
            (r"\bsubtract\s+([a-z_]\w*)\s+from\s+([a-z_]\w*)", r"set \2 to \2 minus \1"),
            (r"\bmultiply\s+([a-z_]\w*)\s+by\s+([a-z_]\w*)", r"set \1 to \1 times \2"),
            (r"\bdivide\s+([a-z_]\w*)\s+by\s+([a-z_]\w*)", r"set \1 to \1 divided by \2"),
            # IO rewrites.
            (r"\bdisplay\s+the\s+value\s+of\s+([a-z_]\w*)", r"print \1"),
            (r"\bdisplay\s+([a-z_]\w*)", r"print \1"),
            (r"\breveal\s+([a-z_]\w*)", r"print \1"),
            (r"\breceive\s+input\s+into\s+([a-z_]\w*)", r"input \1"),
            (r"\btake\s+into\s+([a-z_]\w*)\s+a\s+value", r"input \1"),
            # Control-flow rewrite heads.
            (r"\bwhilst\b", "while"),
            (r"\brepeat\s+the\s+following\s+(\d+)\s+times", r"repeat \1 times"),
        ]

        for pattern, replacement in substitutions:
            normalized = re.sub(pattern, replacement, normalized)

        # Cleanup punctuation and spacing.
        normalized = re.sub(r"\s+,", ",", normalized)
        normalized = re.sub(r",\s*,+", ",", normalized)
        normalized = re.sub(r"\s+", " ", normalized)
        normalized = normalized.strip(" ,")

        if not normalized:
            raise NormalizationError("Normalization produced empty output")

        return normalized

    def _normalize_multi_assign(self, text: str) -> str:
        pattern = re.compile(
            r"\bassign\s+unto\s+([a-z_]\w*)\s+and\s+([a-z_]\w*)\s+the\s+value\s+([^,]+)",
            re.IGNORECASE,
        )

        def repl(match: re.Match[str]) -> str:
            left = match.group(1)
            right = match.group(2)
            value = match.group(3).strip()
            return f"set {left} to {value}, set {right} to {value}"

        return pattern.sub(repl, text)
