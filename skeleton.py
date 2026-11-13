"""
Smart Code Skeletonizer.
Extracts interfaces, classes, function signatures, and docstrings
while omitting implementation details to save up to 80% of tokens.
"""

import ast
import re
from typing import Optional


def extract_python_skeleton(code: str) -> str:
    """Uses Python AST to extract signatures, classes, and docstrings."""
    try:
        tree = ast.parse(code)
    except Exception:
        # Fallback to regex if syntax error (e.g. invalid snippet or newer syntax)
        return _extract_generic_skeleton(code, lang="python")

    class SkeletonTransformer(ast.NodeTransformer):
        def _strip_body(self, body):
            new_body = []
            # Preserve module/class/func docstring if present
            if body and isinstance(body[0], ast.Expr) and isinstance(body[0].value, ast.Constant) and isinstance(body[0].value.value, str):
                new_body.append(body[0])
            new_body.append(ast.Expr(value=ast.Constant(value=Ellipsis)))
            return new_body

        def visit_FunctionDef(self, node: ast.FunctionDef):
            node.body = self._strip_body(node.body)
            return node

        def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef):
            node.body = self._strip_body(node.body)
            return node

        def visit_ClassDef(self, node: ast.ClassDef):
            # Keep class docstring, attributes, and skeletonized methods
            new_body = []
            for item in node.body:
                if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    new_body.append(self.visit(item))
                elif isinstance(item, (ast.AnnAssign, ast.Assign)):
                    # Keep class-level variable annotations
                    new_body.append(item)
                elif isinstance(item, ast.Expr) and isinstance(item.value, ast.Constant) and isinstance(item.value.value, str):
                    new_body.append(item)
            if not new_body:
                new_body = [ast.Expr(value=ast.Constant(value=Ellipsis))]
            node.body = new_body
            return node

    transformed = SkeletonTransformer().visit(tree)
    try:
        return ast.unparse(transformed)
    except Exception:
        return code


def _extract_generic_skeleton(code: str, lang: str = "generic") -> str:
    """Regex-based skeleton extractor for JS/TS, Go, Rust, Java, etc."""
    lines = code.splitlines()
    skeleton_lines = []
    in_block = False
    brace_depth = 0

    # Patterns that represent important architectural declarations
    decl_patterns = [
        re.compile(r"^(export\s+)?(default\s+)?(class|interface|type|enum|struct|trait|impl)\b"),
        re.compile(r"^(export\s+)?(async\s+)?function\b"),
        re.compile(r"^(public|private|protected|static|override|async|fn|func|def)\b"),
        re.compile(r"^(import|export|from|package|use)\b"),
    ]

    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue

        # Keep comments and docstrings
        if stripped.startswith(("//", "/*", "*", "#", "///", "/**")):
            skeleton_lines.append(line)
            continue

        # Check for signature starts
        is_decl = any(p.search(stripped) for p in decl_patterns)
        if is_decl:
            # If function has curly brace, strip body
            if "{" in stripped and "}" in stripped:
                skeleton_lines.append(line)
            elif "{" in stripped:
                skeleton_lines.append(line.split("{")[0].rstrip() + " { /* ... */ }")
            else:
                skeleton_lines.append(line)
        elif stripped.startswith(("import ", "export ", "from ")):
            skeleton_lines.append(line)

    if not skeleton_lines:
        return code  # If nothing matched, don't destroy content

    return "\n".join(skeleton_lines)


def extract_skeleton(code: str, file_path: str) -> str:
    """
    Main entry point for skeletonizing code files based on file extension.
    """
    lower = file_path.lower()
    if lower.endswith(".py"):
        return extract_python_skeleton(code)
    elif lower.endswith((".ts", ".tsx", ".js", ".jsx")):
        return _extract_generic_skeleton(code, lang="ts")
    elif lower.endswith((".go", ".rs", ".java", ".cpp", ".cs")):
        return _extract_generic_skeleton(code, lang="c_family")
    return code
