"""
Output formatters for LLM consumption (Markdown, XML, Plaintext) and directory tree rendering.
"""

from typing import List, Dict, Any


def generate_tree(file_paths: List[str]) -> str:
    """Generates a clean ASCII file tree from a list of relative paths."""
    tree: Dict[str, Any] = {}
    for path in sorted(file_paths):
        parts = path.replace("\\", "/").split("/")
        current = tree
        for part in parts:
            current = current.setdefault(part, {})

    lines = ["."]

    def _render(node: Dict[str, Any], prefix: str = ""):
        keys = list(node.keys())
        for i, key in enumerate(keys):
            is_last = (i == len(keys) - 1)
            connector = "└── " if is_last else "├── "
            lines.append(f"{prefix}{connector}{key}")
            new_prefix = prefix + ("    " if is_last else "│   ")
            _render(node[key], new_prefix)

    _render(tree)
    return "\n".join(lines)


def format_markdown(files: List[Dict[str, str]], tree: str, summary: Dict[str, Any]) -> str:
    """Formats output as clean Markdown for ChatGPT/Claude/Gemini."""
    parts = [
        "# Codebase Context",
        f"> Generated with code2context | Files: {summary['file_count']} | Estimated Tokens: {summary['tokens']:,}",
        "",
        "## Directory Structure",
        "```text",
        tree,
        "```",
        "",
        "## Source Files",
    ]

    for item in files:
        ext = item["path"].split(".")[-1] if "." in item["path"] else ""
        parts.append(f"### `{item['path']}`")
        parts.append(f"```{ext}")
        parts.append(item["content"])
        parts.append("```")
        parts.append("")

    return "\n".join(parts)


def format_xml(files: List[Dict[str, str]], tree: str, summary: Dict[str, Any]) -> str:
    """Formats output using XML tags (ideal for Anthropic Claude)."""
    parts = [
        "<codebase>",
        f"  <summary files=\"{summary['file_count']}\" tokens=\"{summary['tokens']}\" />",
        "  <directory_structure>",
        tree,
        "  </directory_structure>",
        "  <documents>",
    ]

    for item in files:
        parts.append(f"    <document path=\"{item['path']}\">")
        parts.append(f"      <source_code>")
        parts.append(item["content"])
        parts.append(f"      </source_code>")
        parts.append("    </document>")

    parts.append("  </documents>")
    parts.append("</codebase>")
    return "\n".join(parts)
