"""
Core logic for scanning, filtering, skeletonizing, and packing codebase files.
"""

import os
from pathlib import Path
from typing import List, Dict, Any, Optional, Set
import fnmatch

from .skeleton import extract_skeleton
from .tokenizer import estimate_tokens, estimate_costs
from .formatters import generate_tree, format_markdown, format_xml

DEFAULT_IGNORES = [
    # Version control
    ".git", ".svn", ".hg",
    # Dependencies & caches
    "node_modules", "vendor", "__pycache__", ".pytest_cache", ".ruff_cache", ".mypy_cache",
    ".venv", "venv", "env", ".tox", "dist", "build", "*.egg-info",
    # Secrets & Environment variables
    ".env*", "*.env*", "*.pem", "*.key", "*.cert", "*.p12", "id_rsa*", "*credentials*", "*secret*",
    # Binary & heavy assets
    "*.png", "*.jpg", "*.jpeg", "*.gif", "*.ico", "*.webp", "*.svg",
    "*.mp3", "*.mp4", "*.wav", "*.avi", "*.mov",
    "*.exe", "*.dll", "*.so", "*.dylib", "*.bin", "*.iso",
    "*.zip", "*.tar", "*.gz", "*.7z", "*.rar",
    "*.sqlite", "*.sqlite3", "*.db",
    # Lockfiles (usually unneeded context)
    "package-lock.json", "yarn.lock", "pnpm-lock.yaml", "poetry.lock", "Pipfile.lock",
]


def load_gitignore_patterns(root_dir: Path) -> List[str]:
    """Loads patterns from .gitignore if present."""
    patterns = list(DEFAULT_IGNORES)
    gitignore = root_dir / ".gitignore"
    if gitignore.is_file():
        try:
            with open(gitignore, "r", encoding="utf-8", errors="ignore") as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#"):
                        patterns.append(line)
        except Exception:
            pass
    return patterns


def is_ignored(rel_path: str, patterns: List[str]) -> bool:
    """Checks whether a relative path matches ignore patterns."""
    normalized = rel_path.replace("\\", "/")
    parts = normalized.split("/")

    for pattern in patterns:
        clean_pat = pattern.rstrip("/")
        # Check against each folder part or whole path
        for part in parts:
            if fnmatch.fnmatch(part, clean_pat):
                return True
        if fnmatch.fnmatch(normalized, clean_pat) or fnmatch.fnmatch(parts[-1], clean_pat):
            return True
    return False


def is_binary_file(file_path: Path) -> bool:
    """Quick check for binary files by scanning first 1024 bytes."""
    try:
        with open(file_path, "rb") as f:
            chunk = f.read(1024)
            if b"\x00" in chunk:
                return True
    except Exception:
        return True
    return False


def scan_directory(
    root_dir: Path,
    patterns: Optional[List[str]] = None,
    max_file_size_kb: int = 500,
) -> List[Path]:
    """Recursively scans directory returning non-ignored text files."""
    if patterns is None:
        patterns = load_gitignore_patterns(root_dir)

    valid_files: List[Path] = []
    for dirpath, dirnames, filenames in os.walk(root_dir):
        # Prune ignored directories in-place to prevent traversing them
        dir_rel = Path(dirpath).relative_to(root_dir).as_posix()
        if dir_rel != ".":
            if is_ignored(dir_rel, patterns):
                dirnames.clear()
                continue

        # Prune hidden or ignored subdirectories
        dirnames[:] = [d for d in dirnames if not is_ignored((Path(dirpath) / d).relative_to(root_dir).as_posix(), patterns)]

        for fname in filenames:
            fpath = Path(dirpath) / fname
            rel = fpath.relative_to(root_dir).as_posix()

            if is_ignored(rel, patterns):
                continue

            try:
                # Skip large files (> max_file_size_kb)
                if fpath.stat().st_size > (max_file_size_kb * 1024):
                    continue
            except Exception:
                continue

            if not is_binary_file(fpath):
                valid_files.append(fpath)

    return sorted(valid_files)


def pack_codebase(
    target_dir: str | Path,
    output_format: str = "markdown",
    skeleton_mode: bool = False,
    include_tree: bool = True,
    max_file_size_kb: int = 500,
) -> Dict[str, Any]:
    """
    Main function to pack a codebase directory into LLM context.
    """
    root = Path(target_dir).resolve()
    if not root.exists():
        raise ValueError(f"Path does not exist: {root}")

    files = scan_directory(root, max_file_size_kb=max_file_size_kb)
    processed_files: List[Dict[str, str]] = []
    file_rel_paths = []

    total_chars_original = 0
    total_chars_final = 0

    for fpath in files:
        rel = fpath.relative_to(root).as_posix()
        file_rel_paths.append(rel)

        try:
            with open(fpath, "r", encoding="utf-8", errors="replace") as f:
                content = f.read()
        except Exception:
            continue

        total_chars_original += len(content)

        if skeleton_mode:
            content = extract_skeleton(content, rel)

        total_chars_final += len(content)

        processed_files.append({
            "path": rel,
            "content": content,
        })

    tree_str = generate_tree(file_rel_paths) if include_tree else ""

    # Measure tokens on final formatted context
    temp_summary = {"file_count": len(processed_files), "tokens": 0}
    if output_format.lower() == "xml":
        raw_bundle = format_xml(processed_files, tree_str, temp_summary)
    else:
        raw_bundle = format_markdown(processed_files, tree_str, temp_summary)

    token_count = estimate_tokens(raw_bundle)
    costs = estimate_costs(token_count)

    savings_pct = 0.0
    if skeleton_mode and total_chars_original > 0:
        savings_pct = round((1 - (total_chars_final / total_chars_original)) * 100, 1)

    # Final formatted bundle with correct token count
    summary = {
        "file_count": len(processed_files),
        "tokens": token_count,
        "skeleton_savings_pct": savings_pct,
        "costs": costs,
    }

    if output_format.lower() == "xml":
        final_bundle = format_xml(processed_files, tree_str, summary)
    else:
        final_bundle = format_markdown(processed_files, tree_str, summary)

    return {
        "bundle": final_bundle,
        "tree": tree_str,
        "summary": summary,
        "files": processed_files,
    }
