"""Main driver: runs all compiler phases for restricted English input."""

from __future__ import annotations

import argparse
from pprint import pformat

from codegen import CodeGenerator
from ir import IRGenerator
from lexer import Lexer
from optimizer import Optimizer
from parser import Parser
from semantic import SemanticAnalyzer


def compile_text_to_python(text: str) -> str:
    # 1) Lexical analysis
    lexer = Lexer()
    tokens = lexer.tokenize(text)

    # 2) Syntax analysis
    parser = Parser(tokens)
    ast = parser.parse()

    # 3) Semantic analysis
    semantic = SemanticAnalyzer()
    validated_ast = semantic.analyze(ast)

    # 4) IR generation
    ir_gen = IRGenerator()
    ir_instructions = ir_gen.generate(validated_ast)

    # 5) Optimization
    optimizer = Optimizer()
    optimized_ir = optimizer.optimize(ir_instructions)

    # 6) Code generation
    codegen = CodeGenerator()
    python_code = codegen.generate(optimized_ir)

    # Demonstration output for all phases
    print("=== Input Text ===")
    print(text)
    print()

    print("=== Tokens (Lexer Output) ===")
    print(tokens)
    print()

    print("=== AST (Parser Output) ===")
    print(pformat(ast))
    print()

    print("=== Symbol Table (Semantic Output) ===")
    print(semantic.symbol_table)
    print()

    print("=== IR (Before Optimization) ===")
    for inst in ir_instructions:
        print(inst)
    print()

    print("=== IR (After Optimization) ===")
    for inst in optimized_ir:
        print(inst)
    print()

    print("=== Generated Python Code ===")
    print(python_code)
    print()

    return python_code


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Mini compiler from restricted English to Python"
    )
    parser.add_argument(
        "input_text",
        nargs="?",
        default="initialize 'a' and 'b' to 1, add them and store the result in 'c', print 'c'",
        help="Restricted English instruction string",
    )
    parser.add_argument(
        "--execute",
        action="store_true",
        help="Execute generated Python code after compilation",
    )
    args = parser.parse_args()

    python_code = compile_text_to_python(args.input_text)

    if args.execute:
        print("=== Program Output ===")
        exec(python_code, {})


if __name__ == "__main__":
    main()
