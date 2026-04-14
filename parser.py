"""Syntax analysis phase: builds an AST from token stream."""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional

from lexer import Token


class ParserError(Exception):
    """Raised when tokens do not form valid syntax."""


@dataclass
class ASTNode:
    pass


@dataclass
class Program(ASTNode):
    statements: List[ASTNode]


@dataclass
class Init(ASTNode):
    names: List[str]
    value: int


@dataclass
class Add(ASTNode):
    left: str
    right: str
    target: str


@dataclass
class Print(ASTNode):
    name: str


class Parser:
    """Parses token list into an AST for the restricted language."""

    def __init__(self, tokens: List[Token]):
        self.tokens = tokens
        self.pos = 0
        self.last_identifiers: List[str] = []

    def parse(self) -> Program:
        statements: List[ASTNode] = []
        while not self._is_at_end():
            self._skip_commas()
            if self._is_at_end():
                break
            stmt = self._parse_statement()
            statements.append(stmt)
            self._skip_commas()
        return Program(statements=statements)

    def _parse_statement(self) -> ASTNode:
        token = self._peek()
        if token and token.type == "INIT":
            return self._parse_init()
        if token and token.type == "ADD":
            return self._parse_add()
        if token and token.type == "PRINT":
            return self._parse_print()
        raise ParserError(f"Unexpected token at statement start: {token}")

    def _parse_init(self) -> Init:
        self._expect("INIT")
        names = [self._expect("IDENTIFIER").value]
        while self._match("AND"):
            names.append(self._expect("IDENTIFIER").value)
        self._expect("TO")
        value = int(self._expect("NUMBER").value)
        self.last_identifiers = names[:] if names else self.last_identifiers
        return Init(names=names, value=value)

    def _parse_add(self) -> Add:
        self._expect("ADD")

        if self._match("THEM"):
            if len(self.last_identifiers) < 2:
                raise ParserError("'them' cannot be resolved to two identifiers")
            left, right = self.last_identifiers[-2], self.last_identifiers[-1]
        else:
            left = self._expect("IDENTIFIER").value
            self._expect("AND")
            right = self._expect("IDENTIFIER").value

        # Allow optional filler words: and store the result in
        self._expect("AND")
        self._expect("STORE")
        self._expect("THE")
        self._expect("RESULT")
        self._expect("IN")
        target = self._expect("IDENTIFIER").value
        self.last_identifiers = [left, right, target]
        return Add(left=left, right=right, target=target)

    def _parse_print(self) -> Print:
        self._expect("PRINT")
        name = self._expect("IDENTIFIER").value
        self.last_identifiers = [name]
        return Print(name=name)

    def _skip_commas(self) -> None:
        while self._match("COMMA"):
            pass

    def _match(self, token_type: str) -> bool:
        token = self._peek()
        if token and token.type == token_type:
            self.pos += 1
            return True
        return False

    def _expect(self, token_type: str) -> Token:
        token = self._peek()
        if token is None:
            raise ParserError(f"Expected {token_type}, found end of input")
        if token.type != token_type:
            raise ParserError(f"Expected {token_type}, found {token.type} ({token.value})")
        self.pos += 1
        return token

    def _peek(self) -> Optional[Token]:
        if self.pos >= len(self.tokens):
            return None
        return self.tokens[self.pos]

    def _is_at_end(self) -> bool:
        return self.pos >= len(self.tokens)
