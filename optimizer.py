"""Optimization phase: applies lightweight optimizations over IR."""

from __future__ import annotations

from typing import Dict, List, Set

from ir import IRInstruction


class Optimizer:
    """Performs simple constant propagation/folding and temp elimination."""

    def optimize(self, ir_instructions: List[IRInstruction]) -> List[IRInstruction]:
        constants: Dict[str, int] = {}
        optimized: List[IRInstruction] = []

        for inst in ir_instructions:
            if inst.op == "assign_const":
                value = int(inst.arg1)
                constants[inst.result] = value
                optimized.append(inst)
            elif inst.op == "add":
                left_const = self._resolve_constant(inst.arg1, constants)
                right_const = self._resolve_constant(inst.arg2, constants)
                if left_const is not None and right_const is not None:
                    const_sum = left_const + right_const
                    constants[inst.result] = const_sum
                    optimized.append(
                        IRInstruction(op="assign_const", arg1=str(const_sum), result=inst.result)
                    )
                else:
                    constants.pop(inst.result, None)
                    optimized.append(inst)
            elif inst.op == "assign":
                source_const = self._resolve_constant(inst.arg1, constants)
                if source_const is not None:
                    constants[inst.result] = source_const
                    optimized.append(
                        IRInstruction(op="assign_const", arg1=str(source_const), result=inst.result)
                    )
                else:
                    constants.pop(inst.result, None)
                    optimized.append(inst)
            elif inst.op == "print":
                optimized.append(inst)
            else:
                optimized.append(inst)

        return self._remove_unnecessary_temporaries(optimized)

    def _resolve_constant(self, name: str | None, constants: Dict[str, int]) -> int | None:
        if name is None:
            return None
        return constants.get(name)

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
            if inst.arg1:
                used_names.add(inst.arg1)
            if inst.arg2:
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
                    )
                )
                i += 2
                continue

            result.append(current)
            i += 1

        return result
