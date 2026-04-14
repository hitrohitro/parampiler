"""Code generation phase: emits executable Python source from IR."""

from __future__ import annotations

from typing import List

from ir import IRInstruction


class CodeGenerator:
    """Converts IR instructions to Python code lines."""

    def generate(self, ir_instructions: List[IRInstruction]) -> str:
        lines: List[str] = []
        for inst in ir_instructions:
            if inst.op == "assign_const":
                lines.append(f"{inst.result} = {inst.arg1}")
            elif inst.op == "assign":
                lines.append(f"{inst.result} = {inst.arg1}")
            elif inst.op == "add":
                lines.append(f"{inst.result} = {inst.arg1} + {inst.arg2}")
            elif inst.op == "print":
                lines.append(f"print({inst.arg1})")
            else:
                raise ValueError(f"Unsupported IR op during code generation: {inst.op}")

        return "\n".join(lines)
