"""Lexical analysis phase: converts restricted English text into tokens."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import List


@dataclass(frozen=True)
class Token:
    type: str
    value: str

    def __repr__(self) -> str:
        return f"Token(type={self.type!r}, value={self.value!r})"


class LexerError(Exception):
    """Raised when input text cannot be tokenized."""


class Lexer:
    """Tokenizes a restricted English instruction language."""

    KEYWORDS = {
        "initialize": "INIT",
        "add": "ADD",
        "store": "STORE",
        "print": "PRINT",
        "to": "TO",
        "and": "AND",
        "in": "IN",
        "the": "THE",
        "result": "RESULT",
    }

    SPECIAL_IDENTIFIERS = {
        "them": "THEM",
    }

    TOKEN_REGEX = re.compile(
        r"\d+|'[A-Za-z_][A-Za-z_0-9]*'|[A-Za-z_][A-Za-z_0-9]*|,",
        re.IGNORECASE,
    )

    def tokenize(self, text: str) -> List[Token]:
        if not text or not text.strip():
            return []

        raw_tokens = self.TOKEN_REGEX.findall(text)
        tokens: List[Token] = []

        for raw in raw_tokens:
            if raw == ",":
                tokens.append(Token("COMMA", raw))
                continue

            if raw.startswith("'") and raw.endswith("'"):
                identifier = raw[1:-1].lower()
                tokens.append(Token("IDENTIFIER", identifier))
                continue

            lower = raw.lower()

            if lower.isdigit():
                tokens.append(Token("NUMBER", lower))
            elif lower in self.KEYWORDS:
                tokens.append(Token(self.KEYWORDS[lower], lower))
            elif lower in self.SPECIAL_IDENTIFIERS:
                tokens.append(Token(self.SPECIAL_IDENTIFIERS[lower], lower))
            elif re.fullmatch(r"[a-z_][a-z_0-9]*", lower):
                tokens.append(Token("IDENTIFIER", lower))
            else:
                raise LexerError(f"Unrecognized token: {raw}")

        return tokens
