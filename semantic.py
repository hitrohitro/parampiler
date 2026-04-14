"""Semantic analysis phase: validates AST using a symbol table."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict

from parser import Add, Init, Print, Program


class SemanticError(Exception):
    """Raised when semantic rules are violated."""


@dataclass
class SemanticAnalyzer:
    symbol_table: Dict[str, str] = field(default_factory=dict)

    def analyze(self, program: Program) -> Program:
        for stmt in program.statements:
            if isinstance(stmt, Init):
                for name in stmt.names:
                    self.symbol_table[name] = "int"
            elif isinstance(stmt, Add):
                self._ensure_initialized(stmt.left)
                self._ensure_initialized(stmt.right)
                self.symbol_table[stmt.target] = "int"
            elif isinstance(stmt, Print):
                self._ensure_initialized(stmt.name)
            else:
                raise SemanticError(f"Unknown AST node: {stmt}")
        return program

    def _ensure_initialized(self, name: str) -> None:
        if name not in self.symbol_table:
            raise SemanticError(f"Variable '{name}' used before initialization")
