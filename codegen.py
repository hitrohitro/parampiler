"""Code generation phase: emits executable Python source from optimized IR."""

from __future__ import annotations

from typing import List

from ir import IRInstruction


class CodeGenerator:
    """Converts IR instructions to Python code lines."""

    def generate(self, ir_instructions: List[IRInstruction]) -> str:
        lines, _ = self._emit_block(ir_instructions, 0, 0)
        return "\n".join(lines)

    def _emit_block(
        self, ir_instructions: List[IRInstruction], start: int, indent: int
    ) -> tuple[List[str], int]:
        lines: List[str] = []
        i = start

        while i < len(ir_instructions):
            inst = ir_instructions[i]

            if (
                i + 3 < len(ir_instructions)
                and inst.op == "if_false_goto"
                and ir_instructions[i + 1].op not in {"label", "goto"}
            ):
                if_lines, next_index = self._try_emit_if(ir_instructions, i, indent)
                if if_lines is not None:
                    lines.extend(if_lines)
                    i = next_index
                    continue

            # Detect canonical while-loop IR pattern.
            if inst.op == "label":
                loop_lines, next_index = self._try_emit_while(ir_instructions, i, indent)
                if loop_lines is not None:
                    lines.extend(loop_lines)
                    i = next_index
                    continue

            if inst.op == "label":
                # Loop end markers are consumed by parent loop pattern detection.
                break

            # Detect canonical for-loop IR pattern.
            if (
                i + 6 < len(ir_instructions)
                and inst.op == "assign_const"
                and inst.result
                and inst.result.startswith("t")
                and ir_instructions[i + 1].op == "label"
                and ir_instructions[i + 2].op == "binop"
                and ir_instructions[i + 2].arg1 == inst.result
                and ir_instructions[i + 2].arg2 == "0"
                and ir_instructions[i + 2].extra == ">"
                and ir_instructions[i + 3].op == "if_false_goto"
                and ir_instructions[i + 3].arg1 == ir_instructions[i + 2].result
            ):
                loop_lines, next_index = self._try_emit_for(ir_instructions, i, indent)
                if loop_lines is not None:
                    lines.extend(loop_lines)
                    i = next_index
                    continue

            lines.append(self._emit_instruction(inst, indent))
            i += 1

        return lines, i

    def _try_emit_if(
        self, ir_instructions: List[IRInstruction], start: int, indent: int
    ) -> tuple[List[str] | None, int]:
        cond_inst = ir_instructions[start]
        else_label = cond_inst.result

        # Try if-else first
        goto_index = start + 1
        while goto_index < len(ir_instructions):
            cand = ir_instructions[goto_index]
            if cand.op == "goto" and goto_index + 1 < len(ir_instructions):
                l = ir_instructions[goto_index + 1]
                if l.op == "label" and l.arg1 == else_label:
                    end_label = cand.arg1
                    end_label_index = self._find_label(ir_instructions, end_label, goto_index + 2)
                    if end_label_index is not None:
                        then_lines, _ = self._emit_block(ir_instructions[start + 1 : goto_index], 0, indent + 1)
                        else_lines, _ = self._emit_block(
                            ir_instructions[goto_index + 2 : end_label_index], 0, indent + 1
                        )
                        header = f"{'    ' * indent}if {cond_inst.arg1}:"
                        if not then_lines:
                            then_lines = [f"{'    ' * (indent + 1)}pass"]
                        if not else_lines:
                            else_lines = [f"{'    ' * (indent + 1)}pass"]
                        return [header, *then_lines, f"{'    ' * indent}else:", *else_lines], end_label_index + 1
            goto_index += 1

        else_label_index = self._find_label(ir_instructions, else_label, start + 1)
        if else_label_index is None:
            return None, start + 1

        then_lines, _ = self._emit_block(ir_instructions[start + 1 : else_label_index], 0, indent + 1)
        header = f"{'    ' * indent}if {cond_inst.arg1}:"
        if not then_lines:
            then_lines = [f"{'    ' * (indent + 1)}pass"]
        return [header, *then_lines], else_label_index + 1

    def _try_emit_while(
        self, ir_instructions: List[IRInstruction], start: int, indent: int
    ) -> tuple[List[str] | None, int]:
        # Pattern: label Ls; <condition setup>; if_false_goto cond Le; BODY; goto Ls; label Le
        label_inst = ir_instructions[start]
        if label_inst.op != "label":
            return None, start + 1

        start_label = label_inst.arg1
        cond_index = start + 1
        while cond_index < len(ir_instructions) and ir_instructions[cond_index].op != "if_false_goto":
            if ir_instructions[cond_index].op == "label":
                return None, start + 1
            cond_index += 1

        if cond_index >= len(ir_instructions):
            return None, start + 1

        cond_inst = ir_instructions[cond_index]
        end_label = cond_inst.result
        pre_cond = ir_instructions[start + 1 : cond_index]

        j = cond_index + 1
        depth = 0
        while j < len(ir_instructions):
            curr = ir_instructions[j]
            if curr.op == "label" and curr.arg1 == start_label:
                depth += 1
            if curr.op == "goto" and curr.arg1 == start_label and depth == 0:
                if j + 1 < len(ir_instructions) and ir_instructions[j + 1].op == "label" and ir_instructions[j + 1].arg1 == end_label:
                    body_lines, _ = self._emit_block(ir_instructions[cond_index + 1 : j], 0, indent + 1)
                    if pre_cond:
                        pre_cond_lines, _ = self._emit_block(pre_cond, 0, indent + 1)
                        if not body_lines:
                            body_lines = [f"{'    ' * (indent + 1)}pass"]
                        generated = [f"{'    ' * indent}while True:"]
                        generated.extend(pre_cond_lines)
                        generated.append(
                            f"{'    ' * (indent + 1)}if not {cond_inst.arg1}:"
                        )
                        generated.append(f"{'    ' * (indent + 2)}break")
                        generated.extend(body_lines)
                        return generated, j + 2

                    header = f"{'    ' * indent}while {cond_inst.arg1}:"
                    if not body_lines:
                        body_lines = [f"{'    ' * (indent + 1)}pass"]
                    return [header, *body_lines], j + 2
            if curr.op == "label" and curr.arg1 == end_label and depth == 0:
                break
            j += 1

        return None, start + 1

    def _try_emit_for(
        self, ir_instructions: List[IRInstruction], start: int, indent: int
    ) -> tuple[List[str] | None, int]:
        # Pattern: tN = N; label Ls; tM = tN > 0; if_false_goto tM Le; BODY; tN = tN - 1; goto Ls; label Le
        init_inst = ir_instructions[start]
        label_inst = ir_instructions[start + 1]
        cond_calc = ir_instructions[start + 2]
        cond_inst = ir_instructions[start + 3]
        counter = init_inst.result
        start_label = label_inst.arg1
        end_label = cond_inst.result

        j = start + 4
        while j < len(ir_instructions):
            curr = ir_instructions[j]
            if (
                curr.op == "binop"
                and curr.arg1 == counter
                and curr.arg2 == "1"
                and curr.result == counter
                and curr.extra == "-"
            ):
                if (
                    j + 2 < len(ir_instructions)
                    and ir_instructions[j + 1].op == "goto"
                    and ir_instructions[j + 1].arg1 == start_label
                    and ir_instructions[j + 2].op == "label"
                    and ir_instructions[j + 2].arg1 == end_label
                ):
                    body_lines, _ = self._emit_block(ir_instructions[start + 4 : j], 0, indent + 1)
                    header = f"{'    ' * indent}for _ in range({init_inst.arg1}):"
                    if not body_lines:
                        body_lines = [f"{'    ' * (indent + 1)}pass"]
                    return [header, *body_lines], j + 3
            j += 1

        return None, start + 1

    def _emit_instruction(self, inst: IRInstruction, indent: int) -> str:
        prefix = "    " * indent
        if inst.op == "assign_const":
            return f"{prefix}{inst.result} = {inst.arg1}"
        if inst.op == "assign":
            return f"{prefix}{inst.result} = {inst.arg1}"
        if inst.op == "binop":
            return f"{prefix}{inst.result} = {inst.arg1} {inst.extra} {inst.arg2}"
        if inst.op == "unop":
            return f"{prefix}{inst.result} = {inst.extra} {inst.arg1}"
        if inst.op == "input":
            return f"{prefix}{inst.result} = input()"
        if inst.op == "print":
            return f"{prefix}print({inst.arg1})"
        if inst.op == "goto":
            return f"{prefix}# goto {inst.arg1}"
        if inst.op == "if_false_goto":
            return f"{prefix}# if not {inst.arg1}: goto {inst.result}"
        if inst.op == "label":
            return f"{prefix}# label {inst.arg1}"
        raise ValueError(f"Unsupported IR op during code generation: {inst.op}")

    def _find_label(
        self, ir_instructions: List[IRInstruction], label: str | None, start: int
    ) -> int | None:
        if label is None:
            return None
        i = start
        while i < len(ir_instructions):
            inst = ir_instructions[i]
            if inst.op == "label" and inst.arg1 == label:
                return i
            i += 1
        return None
