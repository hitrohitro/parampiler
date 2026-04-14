"""IR generation phase: converts SIE++ AST into three-address code."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional

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


@dataclass
class IRInstruction:
    op: str
    arg1: Optional[str] = None
    arg2: Optional[str] = None
    result: Optional[str] = None
    extra: Optional[str] = None

    def __repr__(self) -> str:
        return (
            "IRInstruction("
            f"op={self.op!r}, arg1={self.arg1!r}, arg2={self.arg2!r}, result={self.result!r}, "
            f"extra={self.extra!r}"
            ")"
        )


class IRGenerator:
    """Generates simple 3-address code instructions."""

    def __init__(self) -> None:
        self.temp_counter = 0
        self.label_counter = 0
        self._last_value = ""
        self.declared_types: Dict[str, str] = {}

    def generate(self, program: ProgramNode) -> List[IRInstruction]:
        instructions: List[IRInstruction] = []
        for stmt in program.statements:
            instructions.extend(self._generate_stmt(stmt))
        return instructions

    def _generate_stmt(self, stmt: object) -> List[IRInstruction]:
        instructions: List[IRInstruction] = []

        if isinstance(stmt, DeclarationNode):
            for name in stmt.names:
                self.declared_types[name] = stmt.var_type
            return instructions

        if isinstance(stmt, AssignmentNode):
            instructions.extend(self._generate_expr(stmt.expr))
            instructions.append(IRInstruction(op="assign", arg1=self._last_value, result=stmt.name))
            return instructions

        if isinstance(stmt, InputNode):
            input_type = self.declared_types.get(stmt.name, "integer")
            instructions.append(IRInstruction(op="input", result=stmt.name, extra=input_type))
            return instructions

        if isinstance(stmt, PrintNode):
            instructions.extend(self._generate_expr(stmt.expr))
            instructions.append(IRInstruction(op="print", arg1=self._last_value))
            return instructions

        if isinstance(stmt, IfNode):
            else_label = self._new_label()
            end_label = self._new_label()

            instructions.extend(self._generate_expr(stmt.condition))
            instructions.append(
                IRInstruction(op="if_false_goto", arg1=self._last_value, result=else_label)
            )
            instructions.extend(self._generate_stmt(stmt.then_branch))

            if stmt.else_branch is not None:
                instructions.append(IRInstruction(op="goto", arg1=end_label))
                instructions.append(IRInstruction(op="label", arg1=else_label))
                instructions.extend(self._generate_stmt(stmt.else_branch))
                instructions.append(IRInstruction(op="label", arg1=end_label))
            else:
                instructions.append(IRInstruction(op="label", arg1=else_label))

            return instructions

        elif isinstance(stmt, WhileNode):
            start_label = self._new_label()
            end_label = self._new_label()
            instructions.append(IRInstruction(op="label", arg1=start_label))
            instructions.extend(self._generate_expr(stmt.condition))
            instructions.append(
                IRInstruction(
                    op="if_false_goto",
                    arg1=self._last_value,
                    result=end_label,
                )
            )
            instructions.extend(self._generate_stmt(stmt.body))
            instructions.append(IRInstruction(op="goto", arg1=start_label))
            instructions.append(IRInstruction(op="label", arg1=end_label))

            return instructions

        if isinstance(stmt, ForNode):
            counter = self._new_temp()
            cond_temp = self._new_temp()
            start_label = self._new_label()
            end_label = self._new_label()

            instructions.append(
                IRInstruction(op="assign_const", arg1=str(stmt.count), result=counter)
            )
            instructions.append(IRInstruction(op="label", arg1=start_label))
            instructions.append(
                IRInstruction(op="binop", arg1=counter, arg2="0", result=cond_temp, extra=">")
            )
            instructions.append(
                IRInstruction(
                    op="if_false_goto",
                    arg1=cond_temp,
                    result=end_label,
                )
            )
            instructions.extend(self._generate_stmt(stmt.body))
            instructions.append(
                IRInstruction(op="binop", arg1=counter, arg2="1", result=counter, extra="-")
            )
            instructions.append(IRInstruction(op="goto", arg1=start_label))
            instructions.append(IRInstruction(op="label", arg1=end_label))

            return instructions

        if isinstance(stmt, BlockNode):
            for nested in stmt.statements:
                instructions.extend(self._generate_stmt(nested))
            return instructions

        raise ValueError(f"Unsupported AST node for IR generation: {stmt}")

    def _generate_expr(self, expr: object) -> List[IRInstruction]:
        out: List[IRInstruction] = []

        if isinstance(expr, NumberNode):
            tmp = self._new_temp()
            out.append(IRInstruction(op="assign_const", arg1=str(expr.value), result=tmp))
            self._last_value = tmp
            return out

        if isinstance(expr, FloatNode):
            tmp = self._new_temp()
            out.append(IRInstruction(op="assign_const", arg1=str(expr.value), result=tmp))
            self._last_value = tmp
            return out

        if isinstance(expr, StringNode):
            tmp = self._new_temp()
            out.append(IRInstruction(op="assign_const", arg1=repr(expr.value), result=tmp))
            self._last_value = tmp
            return out

        if isinstance(expr, BooleanNode):
            tmp = self._new_temp()
            out.append(
                IRInstruction(op="assign_const", arg1="True" if expr.value else "False", result=tmp)
            )
            self._last_value = tmp
            return out

        if isinstance(expr, IdentifierNode):
            self._last_value = expr.name
            return out

        if isinstance(expr, UnaryOpNode):
            out.extend(self._generate_expr(expr.operand))
            operand_value = self._last_value
            tmp = self._new_temp()
            out.append(IRInstruction(op="unop", arg1=operand_value, result=tmp, extra=expr.op))
            self._last_value = tmp
            return out

        if isinstance(expr, BinaryOpNode):
            out.extend(self._generate_expr(expr.left))
            left_value = self._last_value
            out.extend(self._generate_expr(expr.right))
            right_value = self._last_value
            tmp = self._new_temp()
            out.append(
                IRInstruction(
                    op="binop",
                    arg1=left_value,
                    arg2=right_value,
                    result=tmp,
                    extra=expr.op,
                )
            )
            self._last_value = tmp
            return out

        raise ValueError(f"Unsupported expression node: {expr}")

    def _new_temp(self) -> str:
        self.temp_counter += 1
        return f"t{self.temp_counter}"

    def _new_label(self) -> str:
        self.label_counter += 1
        return f"L{self.label_counter}"
