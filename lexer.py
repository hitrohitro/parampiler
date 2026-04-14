"""Lexical analysis phase for Structured Imperative English (SIE++)."""

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
    """Tokenizes SIE++ source text into deterministic tokens."""

    KEYWORDS = {
        "declare": "DECLARE",
        "set": "SET",
        "add": "ADD",
        "if": "IF",
        "otherwise": "OTHERWISE",
        "while": "WHILE",
        "repeat": "REPEAT",
        "begin": "BEGIN",
        "end": "END",
        "input": "INPUT",
        "print": "PRINT",
        "times": "TIMES",
        "to": "TO",
        "and": "AND",
        "or": "OR",
        "not": "NOT",
        "list": "TYPE",
        "map": "TYPE",
        "true": "BOOLEAN",
        "false": "BOOLEAN",
        "plus": "OPERATOR",
        "minus": "OPERATOR",
    }

    SENTINEL_MAP = {
        "<COND_LT>": Token("CONDITION", "<"),
        "<COND_GT>": Token("CONDITION", ">"),
        "<COND_EQ>": Token("CONDITION", "=="),
        "<COND_NE>": Token("CONDITION", "!="),
        "<OP_DIV>": Token("OPERATOR", "/"),
    }

    TOKEN_REGEX = re.compile(
        r"<[^>]+>|\d+\.\d+|\d+|'[^']*'|\"[^\"]*\"|[A-Za-z_][A-Za-z_0-9]*|,",
        re.IGNORECASE,
    )

    def tokenize(self, text: str) -> List[Token]:
        if not text or not text.strip():
            return []

        normalized = self._replace_multiword_phrases(text)
        raw_tokens = self.TOKEN_REGEX.findall(normalized)
        tokens: List[Token] = []

        for raw in raw_tokens:
            if raw == ",":
                tokens.append(Token("COMMA", raw))
                continue

            if raw in self.SENTINEL_MAP:
                tokens.append(self.SENTINEL_MAP[raw])
                continue

            lower = raw.lower()

            if re.fullmatch(r"\d+\.\d+", lower):
                tokens.append(Token("FLOAT", lower))
            elif lower.isdigit():
                tokens.append(Token("NUMBER", lower))
            elif (raw.startswith("'") and raw.endswith("'")) or (
                raw.startswith('"') and raw.endswith('"')
            ):
                tokens.append(Token("STRING", raw[1:-1]))
            elif lower in self.KEYWORDS:
                token_type = self.KEYWORDS[lower]
                tokens.append(Token(token_type, self._keyword_value(lower, token_type)))
            elif re.fullmatch(r"[a-z_][a-z_0-9]*", lower):
                tokens.append(Token("IDENTIFIER", lower))
            else:
                raise LexerError(f"Unrecognized token: {raw}")

        return tokens

    def _replace_multiword_phrases(self, text: str) -> str:
        replaced = text
        replaced = re.sub(r"\bis\s+less\s+than\b", " <COND_LT> ", replaced, flags=re.IGNORECASE)
        replaced = re.sub(
            r"\bis\s+greater\s+than\b", " <COND_GT> ", replaced, flags=re.IGNORECASE
        )
        replaced = re.sub(r"\bis\s+equal\s+to\b", " <COND_EQ> ", replaced, flags=re.IGNORECASE)
        replaced = re.sub(
            r"\bis\s+not\s+equal\s+to\b", " <COND_NE> ", replaced, flags=re.IGNORECASE
        )
        replaced = re.sub(r"\bdivided\s+by\b", " <OP_DIV> ", replaced, flags=re.IGNORECASE)
        return replaced

    def _keyword_value(self, raw_text: str, token_type: str) -> str:
        if token_type == "OPERATOR":
            if raw_text == "plus":
                return "+"
            if raw_text == "minus":
                return "-"
        return raw_text
