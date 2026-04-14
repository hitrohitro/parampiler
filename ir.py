"""IR generation phase: converts AST into three-address code."""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional

from parser import Add, Init, Print, Program


@dataclass
class IRInstruction:
    op: str
    arg1: Optional[str] = None
    arg2: Optional[str] = None
    result: Optional[str] = None

    def __repr__(self) -> str:
        return (
            "IRInstruction("
            f"op={self.op!r}, arg1={self.arg1!r}, arg2={self.arg2!r}, result={self.result!r}"
            ")"
        )


class IRGenerator:
    """Generates simple 3-address code instructions."""

    def __init__(self) -> None:
        self.temp_counter = 0

    def generate(self, program: Program) -> List[IRInstruction]:
        instructions: List[IRInstruction] = []
        for stmt in program.statements:
            if isinstance(stmt, Init):
                for name in stmt.names:
                    instructions.append(
                        IRInstruction(op="assign_const", arg1=str(stmt.value), result=name)
                    )
            elif isinstance(stmt, Add):
                temp = self._new_temp()
                instructions.append(
                    IRInstruction(op="add", arg1=stmt.left, arg2=stmt.right, result=temp)
                )
                instructions.append(
                    IRInstruction(op="assign", arg1=temp, result=stmt.target)
                )
            elif isinstance(stmt, Print):
                instructions.append(IRInstruction(op="print", arg1=stmt.name))
            else:
                raise ValueError(f"Unsupported AST node for IR generation: {stmt}")
        return instructions

    def _new_temp(self) -> str:
        self.temp_counter += 1
        return f"t{self.temp_counter}"
