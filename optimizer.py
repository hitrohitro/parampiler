"""Optimization phase for SIE++ IR.

Performs constant folding/propagation and lightweight dead code elimination.
"""

from __future__ import annotations

from typing import Dict, List, Set

from ir import IRInstruction


class Optimizer:
    """Performs simple constant propagation/folding and temp elimination."""

    def optimize(self, ir_instructions: List[IRInstruction]) -> List[IRInstruction]:
        constants: Dict[str, str] = {}
        optimized: List[IRInstruction] = []

        for inst in ir_instructions:
            if inst.op == "assign_const":
                constants[inst.result] = inst.arg1
                optimized.append(inst)
            elif inst.op == "assign":
                src = self._replace_const(inst.arg1, constants)
                if self._is_literal(src):
                    constants[inst.result] = src
                    optimized.append(IRInstruction(op="assign_const", arg1=src, result=inst.result))
                else:
                    constants.pop(inst.result, None)
                    optimized.append(IRInstruction(op="assign", arg1=src, result=inst.result))
            elif inst.op == "unop":
                arg = self._replace_const(inst.arg1, constants)
                folded = self._fold_unary(inst.extra, arg)
                if folded is not None:
                    constants[inst.result] = folded
                    optimized.append(IRInstruction(op="assign_const", arg1=folded, result=inst.result))
                else:
                    constants.pop(inst.result, None)
                    optimized.append(IRInstruction(op="unop", arg1=arg, result=inst.result, extra=inst.extra))
            elif inst.op == "binop":
                arg1 = self._replace_const(inst.arg1, constants)
                arg2 = self._replace_const(inst.arg2, constants)
                folded = self._fold_binary(inst.extra, arg1, arg2)
                if folded is not None:
                    constants[inst.result] = folded
                    optimized.append(IRInstruction(op="assign_const", arg1=folded, result=inst.result))
                else:
                    constants.pop(inst.result, None)
                    optimized.append(
                        IRInstruction(
                            op="binop", arg1=arg1, arg2=arg2, result=inst.result, extra=inst.extra
                        )
                    )
            elif inst.op == "if_false_goto":
                cond = self._replace_const(inst.arg1, constants)
                optimized.append(IRInstruction(op="if_false_goto", arg1=cond, result=inst.result))
                constants.clear()
            elif inst.op in {"label", "goto", "input"}:
                constants.clear()
                optimized.append(inst)
            elif inst.op == "print":
                arg = self._replace_const(inst.arg1, constants)
                optimized.append(IRInstruction(op="print", arg1=arg))
            else:
                optimized.append(inst)

        optimized = self._remove_unnecessary_temporaries(optimized)
        return self._remove_redundant_gotos(optimized)

    def _replace_const(self, value: str | None, constants: Dict[str, str]) -> str | None:
        if value is None:
            return None
        return constants.get(value, value)

    def _is_literal(self, value: str | None) -> bool:
        if value is None:
            return False
        if value in {"True", "False"}:
            return True
        if (value.startswith("'") and value.endswith("'")) or (
            value.startswith('"') and value.endswith('"')
        ):
            return True
        if value.count(".") == 1 and value.replace(".", "", 1).lstrip("-").isdigit():
            return True
        return value.lstrip("-").isdigit()

    def _fold_unary(self, op: str | None, arg: str | None) -> str | None:
        if op != "not" or arg not in {"True", "False"}:
            return None
        return "False" if arg == "True" else "True"

    def _fold_binary(self, op: str | None, left: str | None, right: str | None) -> str | None:
        if left is None or right is None or op is None:
            return None
        if not self._is_literal(left) or not self._is_literal(right):
            return None

        try:
            if left in {"True", "False"} or right in {"True", "False"}:
                lval = left == "True"
                rval = right == "True"
            else:
                lval = int(left)
                rval = int(right)

            if op == "+":
                return str(int(lval) + int(rval))
            if op == "-":
                return str(int(lval) - int(rval))
            if op == "*":
                return str(int(lval) * int(rval))
            if op == "/":
                return str(int(lval) // int(rval))
            if op == "<":
                return "True" if int(lval) < int(rval) else "False"
            if op == ">":
                return "True" if int(lval) > int(rval) else "False"
            if op == "==":
                return "True" if lval == rval else "False"
            if op == "!=":
                return "True" if lval != rval else "False"
            if op == "and":
                return "True" if bool(lval) and bool(rval) else "False"
            if op == "or":
                return "True" if bool(lval) or bool(rval) else "False"
        except Exception:
            return None

        return None

    def _remove_unnecessary_temporaries(
        self, ir_instructions: List[IRInstruction]
    ) -> List[IRInstruction]:
        temp_names = {
            inst.result
            for inst in ir_instructions
            if inst.result is not None and inst.result.startswith("t")
        }
        used_names: Set[str] = set()

        for inst in ir_instructions:
            if inst.arg1 and not self._is_literal(inst.arg1):
                used_names.add(inst.arg1)
            if inst.arg2 and not self._is_literal(inst.arg2):
                used_names.add(inst.arg2)

        # Remove dead temp assignments that are never read.
        compacted: List[IRInstruction] = []
        for inst in ir_instructions:
            if inst.result in temp_names and inst.result not in used_names:
                continue
            compacted.append(inst)

        # Rewrite pattern: tX = expr; y = tX -> y = expr
        result: List[IRInstruction] = []
        i = 0
        while i < len(compacted):
            current = compacted[i]
            if (
                current.result
                and current.result.startswith("t")
                and i + 1 < len(compacted)
                and compacted[i + 1].op == "assign"
                and compacted[i + 1].arg1 == current.result
            ):
                nxt = compacted[i + 1]
                result.append(
                    IRInstruction(
                        op=current.op,
                        arg1=current.arg1,
                        arg2=current.arg2,
                        result=nxt.result,
                        extra=current.extra,
                    )
                )
                i += 2
                continue

            result.append(current)
            i += 1

        return result

    def _remove_redundant_gotos(self, ir_instructions: List[IRInstruction]) -> List[IRInstruction]:
        result: List[IRInstruction] = []
        i = 0
        while i < len(ir_instructions):
            current = ir_instructions[i]
            if (
                current.op == "goto"
                and i + 1 < len(ir_instructions)
                and ir_instructions[i + 1].op == "label"
                and ir_instructions[i + 1].arg1 == current.arg1
            ):
                i += 1
                continue
            result.append(current)
            i += 1
        return result
