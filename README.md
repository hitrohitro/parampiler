# Parampiler

A mini compiler that converts restricted English instructions into executable Python code.

## Files

- `lexer.py`: Lexical analysis (text -> tokens)
- `parser.py`: Syntax analysis (tokens -> AST)
- `semantic.py`: Semantic analysis (symbol validation)
- `ir.py`: IR generation (AST -> 3-address code)
- `optimizer.py`: IR optimization
- `codegen.py`: Python code generation
- `main.py`: Pipeline driver and demonstration output

## Example

```bash
python main.py "initialize 'a' and 'b' to 1, add them and store the result in 'c', print 'c'" --execute
```
