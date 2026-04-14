# Parampiler

Parampiler is a dual-frontend mini compiler:

- Standard frontend: Structured Imperative English (SIE++)
- Stylistic frontend: Victorian Controlled English (VCE), normalized into SIE++

The compiler runs a full pipeline and emits executable Python code.

## Project Files

- `mode_handler.py`: mode selection and automatic frontend detection
- `normalizer.py`: Victorian -> SIE++ normalization (Step 0)
- `lexer.py`: lexical analysis
- `parser.py`: syntax analysis and AST construction
- `semantic.py`: semantic analysis with dynamic typing checks
- `ir.py`: intermediate representation (3-address code)
- `optimizer.py`: IR optimizations
- `codegen.py`: Python code generation
- `main.py`: pipeline driver and execution

## Compiler Pipeline

`Input (standard or victorian) -> Mode Handling -> Normalization (victorian only) -> Tokens -> AST -> Semantic -> IR -> Optimized IR -> Python`

## Input Modes

- `--mode standard`
- `--mode victorian`
- `--mode auto` (default, detects Victorian keywords)

## Run Examples

Standard input file:

```bash
python main.py --mode standard --input-file input.txt --execute
```

Victorian input file:

```bash
python main.py --mode victorian --input-file victorian_input.txt --execute
```

Auto-detected mode:

```bash
python main.py --mode auto --input-file victorian_input.txt --execute
```

## Typing Rules

- Basic values are inferred dynamically: integer, float, boolean, string.
- Variables may change basic type across assignments.
- Explicit declarations are only for collections: `list`, `set`, `map`.
