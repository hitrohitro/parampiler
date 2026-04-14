"""Syntax analysis phase: builds an AST from SIE++ tokens."""

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
class ProgramNode(ASTNode):
    statements: List[ASTNode]


@dataclass
class DeclarationNode(ASTNode):
    var_type: str
    names: List[str]


@dataclass
class AssignmentNode(ASTNode):
    name: str
    expr: ASTNode


@dataclass
class BinaryOpNode(ASTNode):
    op: str
    left: ASTNode
    right: ASTNode


@dataclass
class UnaryOpNode(ASTNode):
    op: str
    operand: ASTNode


@dataclass
class IdentifierNode(ASTNode):
    name: str


@dataclass
class NumberNode(ASTNode):
    value: int


@dataclass
class FloatNode(ASTNode):
    value: float


@dataclass
class StringNode(ASTNode):
    value: str


@dataclass
class BooleanNode(ASTNode):
    value: bool


@dataclass
class IfNode(ASTNode):
    condition: ASTNode
    then_branch: ASTNode
    else_branch: Optional[ASTNode] = None


@dataclass
class WhileNode(ASTNode):
    condition: ASTNode
    body: ASTNode


@dataclass
class ForNode(ASTNode):
    count: int
    body: ASTNode


@dataclass
class BlockNode(ASTNode):
    statements: List[ASTNode]


@dataclass
class PrintNode(ASTNode):
    expr: ASTNode


@dataclass
class InputNode(ASTNode):
    name: str


class Parser:
    """Parses token list into an AST for SIE++."""

    def __init__(self, tokens: List[Token]):
        self.tokens = tokens
        self.pos = 0
    def parse(self) -> ProgramNode:
        statements = self._parse_statement_list(stop_tokens=set())
        return ProgramNode(statements=statements)

    def _parse_statement(self) -> ASTNode:
        token = self._peek()
        if token is None:
            raise ParserError("Unexpected end of input while parsing statement")

        if token.type == "DECLARE":
            return self._parse_declaration()
        if token.type == "SET":
            return self._parse_assignment()
        if token.type == "ADD":
            return self._parse_add_statement()
        if token.type == "IF":
            return self._parse_if()
        if token.type == "WHILE":
            return self._parse_while()
        if token.type == "REPEAT":
            return self._parse_for()
        if token.type == "BEGIN":
            return self._parse_block()
        if token.type == "PRINT":
            return self._parse_print()
        if token.type == "INPUT":
            return self._parse_input()

        raise ParserError(f"Unexpected token at statement start: {token}")

    def _parse_statement_list(self, stop_tokens: set[str]) -> List[ASTNode]:
        statements: List[ASTNode] = []
        self._skip_commas()
        while not self._is_at_end():
            nxt = self._peek()
            if nxt and nxt.type in stop_tokens:
                break
            statements.append(self._parse_statement())
            self._skip_commas()
        return statements

    def _parse_declaration(self) -> DeclarationNode:
        self._expect("DECLARE")
        type_token = self._peek()
        if type_token is None:
            raise ParserError("Expected collection type after DECLARE")
        if type_token.type == "TYPE":
            var_type = self._expect("TYPE").value
        elif type_token.type == "SET":
            # 'declare set x' uses SET as a keyword elsewhere, so allow it here contextually.
            var_type = self._expect("SET").value
        else:
            raise ParserError(
                f"Expected collection type (list, set, map), found {type_token.type}"
            )
        names = [self._expect("IDENTIFIER").value]
        while self._match("AND"):
            names.append(self._expect("IDENTIFIER").value)
        return DeclarationNode(var_type=var_type, names=names)

    def _parse_assignment(self) -> AssignmentNode:
        self._expect("SET")
        name = self._expect("IDENTIFIER").value
        self._expect("TO")
        expr = self._parse_expression()
        return AssignmentNode(name=name, expr=expr)

    def _parse_add_statement(self) -> AssignmentNode:
        self._expect("ADD")
        value_expr = self._parse_factor()
        self._expect("TO")
        target = self._expect("IDENTIFIER").value
        expr = BinaryOpNode(op="+", left=IdentifierNode(name=target), right=value_expr)
        return AssignmentNode(name=target, expr=expr)

    def _parse_if(self) -> IfNode:
        self._expect("IF")
        condition = self._parse_expression()
        self._expect("COMMA")
        then_branch = self._parse_statement()

        else_branch: Optional[ASTNode] = None
        if self._match("COMMA"):
            if self._match("OTHERWISE"):
                self._expect("COMMA")
                else_branch = self._parse_statement()
            else:
                self.pos -= 1

        return IfNode(condition=condition, then_branch=then_branch, else_branch=else_branch)

    def _parse_while(self) -> WhileNode:
        self._expect("WHILE")
        condition = self._parse_expression()
        self._expect("COMMA")
        body = self._parse_statement()
        return WhileNode(condition=condition, body=body)

    def _parse_for(self) -> ForNode:
        self._expect("REPEAT")
        count = int(self._expect("NUMBER").value)
        self._expect("TIMES")
        self._expect("COMMA")
        body = self._parse_statement()
        return ForNode(count=count, body=body)

    def _parse_block(self) -> BlockNode:
        self._expect("BEGIN")
        statements = self._parse_statement_list(stop_tokens={"END"})
        self._expect("END")
        return BlockNode(statements=statements)

    def _parse_print(self) -> PrintNode:
        self._expect("PRINT")
        expr = self._parse_expression()
        return PrintNode(expr=expr)

    def _parse_input(self) -> InputNode:
        self._expect("INPUT")
        name = self._expect("IDENTIFIER").value
        return InputNode(name=name)

    def _parse_expression(self) -> ASTNode:
        return self._parse_or()

    def _parse_or(self) -> ASTNode:
        node = self._parse_and()
        while self._match("OR"):
            right = self._parse_and()
            node = BinaryOpNode(op="or", left=node, right=right)
        return node

    def _parse_and(self) -> ASTNode:
        node = self._parse_not()
        while self._match("AND"):
            right = self._parse_not()
            node = BinaryOpNode(op="and", left=node, right=right)
        return node

    def _parse_not(self) -> ASTNode:
        if self._match("NOT"):
            return UnaryOpNode(op="not", operand=self._parse_not())
        return self._parse_comparison()

    def _parse_comparison(self) -> ASTNode:
        left = self._parse_arithmetic()
        if self._peek() and self._peek().type == "CONDITION":
            op = self._expect("CONDITION").value
            right = self._parse_arithmetic()
            return BinaryOpNode(op=op, left=left, right=right)
        return left

    def _parse_arithmetic(self) -> ASTNode:
        node = self._parse_term()
        while self._peek() and self._peek().type == "OPERATOR" and self._peek().value in {
            "+",
            "-",
        }:
            op = self._expect("OPERATOR").value
            right = self._parse_term()
            node = BinaryOpNode(op=op, left=node, right=right)
        return node

    def _parse_term(self) -> ASTNode:
        node = self._parse_factor()
        while True:
            token = self._peek()
            if token and ((token.type == "OPERATOR" and token.value in {"*", "/"}) or token.type == "TIMES"):
                op = "*" if token.type == "TIMES" else token.value
                self.pos += 1
                right = self._parse_factor()
                node = BinaryOpNode(op=op, left=node, right=right)
            else:
                break
        return node

    def _parse_factor(self) -> ASTNode:
        token = self._peek()
        if token is None:
            raise ParserError("Unexpected end of input while parsing expression")

        if token.type == "NUMBER":
            return NumberNode(value=int(self._expect("NUMBER").value))
        if token.type == "FLOAT":
            return FloatNode(value=float(self._expect("FLOAT").value))
        if token.type == "STRING":
            return StringNode(value=self._expect("STRING").value)
        if token.type == "BOOLEAN":
            raw = self._expect("BOOLEAN").value
            return BooleanNode(value=raw == "true")
        if token.type == "IDENTIFIER":
            return IdentifierNode(name=self._expect("IDENTIFIER").value)

        raise ParserError(f"Unexpected token in expression: {token}")

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


# Backward-compatible aliases from earlier versions.
Program = ProgramNode
