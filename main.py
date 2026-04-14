"""Main driver: runs all SIE++ compiler phases end-to-end."""

from __future__ import annotations

import argparse
import sys
from pprint import pformat

from codegen import CodeGenerator
from ir import IRGenerator
from lexer import Lexer, LexerError
from mode_handler import ModeError, ModeHandler
from normalizer import NormalizationError, Normalizer
from optimizer import Optimizer
from parser import Parser, ParserError
from semantic import SemanticAnalyzer, SemanticError


def compile_sie_to_python(sie_text: str) -> str:
    # 1) Lexical analysis
    lexer = Lexer()
    tokens = lexer.tokenize(sie_text)

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

    return python_code, tokens, ast, semantic.symbol_table, ir_instructions, optimized_ir


def print_phase_outputs(
    original_text: str,
    mode: str,
    normalized_text: str,
    tokens: list,
    ast: object,
    symbol_table: dict,
    ir_instructions: list,
    optimized_ir: list,
    python_code: str,
) -> None:
    print("=== Input Mode ===")
    print(mode)
    print()

    # Demonstration output for all phases
    print("=== Original Input Text ===")
    print(original_text)
    print()

    print("=== Normalized SIE++ Text (Step 0) ===")
    print(normalized_text)
    print()

    print("=== Tokens (Lexer Output) ===")
    print(tokens)
    print()

    print("=== AST (Parser Output) ===")
    print(pformat(ast))
    print()

    print("=== Symbol Table (Semantic Output) ===")
    print(symbol_table)
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


def read_input_text(file_path: str) -> str:
    with open(file_path, "r", encoding="utf-8") as source_file:
        text = source_file.read().strip()

    if not text:
        raise ValueError(f"Input file is empty: {file_path}")

    return text


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Mini compiler from Structured Imperative English (SIE++) to Python"
    )
    parser.add_argument(
        "--mode",
        default="auto",
        choices=["auto", "standard", "victorian"],
        help="Input frontend mode: auto, standard, or victorian",
    )
    parser.add_argument(
        "--input-text",
        help="SIE++ source text provided directly as a single string",
    )
    parser.add_argument(
        "--input-file",
        default="input.txt",
        help="Path to a text file containing SIE++ instructions",
    )
    parser.add_argument(
        "--execute",
        action="store_true",
        help="Execute generated Python code after compilation",
    )
    args = parser.parse_args()

    try:
        if args.input_text:
            input_text = args.input_text.strip()
        else:
            input_text = read_input_text(args.input_file)

        mode_handler = ModeHandler()
        decision = mode_handler.decide_mode(input_text, args.mode)

        if decision.mode == "victorian":
            normalizer = Normalizer()
            normalized_text = normalizer.normalize(input_text)
        else:
            normalized_text = input_text

        (
            python_code,
            tokens,
            ast,
            symbol_table,
            ir_instructions,
            optimized_ir,
        ) = compile_sie_to_python(normalized_text)

        print_phase_outputs(
            original_text=input_text,
            mode=decision.mode,
            normalized_text=normalized_text,
            tokens=tokens,
            ast=ast,
            symbol_table=symbol_table,
            ir_instructions=ir_instructions,
            optimized_ir=optimized_ir,
            python_code=python_code,
        )

        if args.execute:
            print("=== Program Output ===")
            exec(python_code, {})
    except (FileNotFoundError, ValueError) as exc:
        print(f"Input Error: {exc}")
        sys.exit(1)
    except NormalizationError as exc:
        print(f"Normalization Error: {exc}")
        sys.exit(1)
    except ModeError as exc:
        print(f"Mode Error: {exc}")
        sys.exit(1)
    except (LexerError, ParserError, SemanticError) as exc:
        print(f"Compilation Error: {exc}")
        sys.exit(1)
    except Exception as exc:
        print(f"Runtime Error: {exc}")
        sys.exit(1)


if __name__ == "__main__":
    main()
