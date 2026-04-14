"""Semantic analysis phase for SIE++.

Tracks declarations, types, and initialization state while validating AST usage.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict

from parser import (
    AssignmentNode,
    BinaryOpNode,
    BlockNode,
    BooleanNode,
    DeclarationNode,
    FloatNode,
    ForNode,
    IdentifierNode,
    IfNode,
    InputNode,
    NumberNode,
    PrintNode,
    ProgramNode,
    StringNode,
    UnaryOpNode,
    WhileNode,
)


class SemanticError(Exception):
    """Raised when semantic rules are violated."""


@dataclass
class SemanticAnalyzer:
    symbol_table: Dict[str, str] = field(default_factory=dict)
    initialized: Dict[str, bool] = field(default_factory=dict)
    collections: Dict[str, str] = field(default_factory=dict)

    def analyze(self, program: ProgramNode) -> ProgramNode:
        for stmt in program.statements:
            self._analyze_statement(stmt)
        return program

    def _analyze_statement(self, stmt: object) -> None:
        if isinstance(stmt, DeclarationNode):
            if stmt.var_type not in {"list", "set", "map"}:
                raise SemanticError(
                    "Only collection declarations are explicit in dynamic mode: list, set, map"
                )
            for name in stmt.names:
                if name in self.symbol_table:
                    raise SemanticError(f"Variable '{name}' is already declared")
                self.symbol_table[name] = stmt.var_type
                self.initialized[name] = False
                self.collections[name] = stmt.var_type
            return

        if isinstance(stmt, AssignmentNode):
            expr_type = self._infer_expr_type(stmt.expr)

            if stmt.name in self.collections:
                target_type = self.collections[stmt.name]
                if expr_type != target_type:
                    raise SemanticError(
                        f"Collection variable '{stmt.name}' must remain type {target_type}, got {expr_type}"
                    )
            else:
                # Dynamic typing for basic variables: infer/update type on every assignment.
                self.symbol_table[stmt.name] = expr_type
                self.initialized[stmt.name] = True

            self.initialized[stmt.name] = True
            return

        if isinstance(stmt, InputNode):
            if stmt.name in self.collections:
                raise SemanticError(
                    f"Cannot assign raw input directly to collection variable '{stmt.name}'"
                )
            self.symbol_table[stmt.name] = "string"
            self.initialized[stmt.name] = True
            return

        if isinstance(stmt, PrintNode):
            self._infer_expr_type(stmt.expr)
            return

        if isinstance(stmt, IfNode):
            cond_type = self._infer_expr_type(stmt.condition)
            if cond_type != "boolean":
                raise SemanticError("If condition must be boolean")
            self._analyze_statement(stmt.then_branch)
            if stmt.else_branch is not None:
                self._analyze_statement(stmt.else_branch)
            return

        if isinstance(stmt, WhileNode):
            cond_type = self._infer_expr_type(stmt.condition)
            if cond_type != "boolean":
                raise SemanticError("While condition must be boolean")
            self._analyze_statement(stmt.body)
            return

        if isinstance(stmt, ForNode):
            if stmt.count <= 0:
                raise SemanticError("Repeat count must be a positive integer")
            self._analyze_statement(stmt.body)
            return

        if isinstance(stmt, BlockNode):
            for item in stmt.statements:
                self._analyze_statement(item)
            return

        raise SemanticError(f"Unknown AST node: {stmt}")

    def _infer_expr_type(self, expr: object) -> str:
        if isinstance(expr, NumberNode):
            return "integer"
        if isinstance(expr, FloatNode):
            return "float"
        if isinstance(expr, StringNode):
            return "string"
        if isinstance(expr, BooleanNode):
            return "boolean"
        if isinstance(expr, IdentifierNode):
            self._ensure_declared(expr.name)
            if not self.initialized.get(expr.name, False):
                raise SemanticError(f"Variable '{expr.name}' used before initialization")
            return self.symbol_table[expr.name]
        if isinstance(expr, UnaryOpNode):
            if expr.op != "not":
                raise SemanticError(f"Unsupported unary operator: {expr.op}")
            operand_type = self._infer_expr_type(expr.operand)
            if operand_type != "boolean":
                raise SemanticError("Operator 'not' requires a boolean operand")
            return "boolean"
        if isinstance(expr, BinaryOpNode):
            left_type = self._infer_expr_type(expr.left)
            right_type = self._infer_expr_type(expr.right)

            if expr.op in {"+", "-", "*", "/"}:
                return self._numeric_result_type(expr.op, left_type, right_type)

            if expr.op in {"<", ">"}:
                if not self._is_numeric(left_type) or not self._is_numeric(right_type):
                    raise SemanticError(
                        f"Relational operator '{expr.op}' requires numeric operands"
                    )
                return "boolean"

            if expr.op in {"==", "!="}:
                if left_type != right_type:
                    raise SemanticError(
                        f"Comparison operator '{expr.op}' requires operands of same type"
                    )
                return "boolean"

            if expr.op in {"and", "or"}:
                if left_type != "boolean" or right_type != "boolean":
                    raise SemanticError(
                        f"Boolean operator '{expr.op}' requires boolean operands"
                    )
                return "boolean"

            raise SemanticError(f"Unsupported binary operator: {expr.op}")

        raise SemanticError(f"Unknown expression node: {expr}")

    def _ensure_declared(self, name: str) -> None:
        if name not in self.symbol_table:
            raise SemanticError(f"Variable '{name}' is not declared")

    def _is_numeric(self, value_type: str) -> bool:
        return value_type in {"integer", "float", "boolean"}

    def _numeric_result_type(self, op: str, left_type: str, right_type: str) -> str:
        if op == "+" and left_type == "string" and right_type == "string":
            return "string"

        if not self._is_numeric(left_type) or not self._is_numeric(right_type):
            raise SemanticError(
                f"Arithmetic operator '{op}' requires numeric operands (or string + string)"
            )

        if op == "/":
            return "float"
        if "float" in {left_type, right_type}:
            return "float"
        return "integer"
