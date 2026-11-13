"""
CLI interface for code2context.
"""

import sys
import argparse
import subprocess
from pathlib import Path

from . import __version__
from .core import pack_codebase


def copy_to_clipboard(text: str) -> bool:
    """Copies text to clipboard using pyperclip or native OS tools."""
    try:
        import pyperclip
        pyperclip.copy(text)
        return True
    except Exception:
        pass

    # Windows fallback
    if sys.platform == "win32":
        try:
            p = subprocess.Popen(["clip"], stdin=subprocess.PIPE, shell=True)
            p.communicate(input=text.encode("utf-8"))
            return p.returncode == 0
        except Exception:
            pass
    # macOS fallback
    elif sys.platform == "darwin":
        try:
            p = subprocess.Popen(["pbcopy"], stdin=subprocess.PIPE)
            p.communicate(input=text.encode("utf-8"))
            return p.returncode == 0
        except Exception:
            pass
    # Linux fallback
    elif sys.platform.startswith("linux"):
        for tool in [["xclip", "-selection", "clipboard"], ["xsel", "--clipboard", "--input"]]:
            try:
                p = subprocess.Popen(tool, stdin=subprocess.PIPE)
                p.communicate(input=text.encode("utf-8"))
                if p.returncode == 0:
                    return True
            except Exception:
                continue

    return False


def main():
    parser = argparse.ArgumentParser(
        prog="code2context",
        description="Pack, skeletonize, and optimize any repository into LLM-ready context with token & cost estimates.",
    )
    parser.add_argument("path", nargs="?", default=".", help="Target directory to pack (default: current directory)")
    parser.add_argument("-o", "--output", help="Write output context bundle to a file")
    parser.add_argument("-s", "--skeleton", action="store_true", help="Extract code skeletons (signatures only) to save up to 80% tokens")
    parser.add_argument("-f", "--format", choices=["markdown", "xml"], default="markdown", help="Output format: markdown (ChatGPT/Gemini) or xml (Claude)")
    parser.add_argument("-c", "--copy", action="store_true", help="Copy context bundle directly to system clipboard")
    parser.add_argument("--no-tree", action="store_true", help="Exclude directory tree from output")
    parser.add_argument("--max-size", type=int, default=500, help="Max file size in KB to include (default: 500)")
    parser.add_argument("-v", "--version", action="version", version=f"%(prog)s {__version__}")
    parser.add_argument("--web", "--serve", action="store_true", help="Launch the Web SaaS Dashboard & API server locally")
    parser.add_argument("--port", type=int, default=8080, help="Port for the Web SaaS server (default: 8080)")

    args = parser.parse_args()

    if args.web:
        from .server import start_server
        start_server(port=args.port)
        return

    target_dir = Path(args.path).resolve()
    if not target_dir.exists():
        print(f"Error: Path '{target_dir}' does not exist.", file=sys.stderr)
        sys.exit(1)

    print(f"\n[code2context v{__version__}]")
    print(f"Analyzing codebase at: {target_dir}")
    if args.skeleton:
        print("  -> Skeleton mode enabled (signatures & docstrings only)")

    try:
        result = pack_codebase(
            target_dir=target_dir,
            output_format=args.format,
            skeleton_mode=args.skeleton,
            include_tree=not args.no_tree,
            max_file_size_kb=args.max_size,
        )
    except Exception as e:
        print(f"Error packing codebase: {e}", file=sys.stderr)
        sys.exit(1)

    summary = result["summary"]
    bundle = result["bundle"]

    print("\n--- Summary ---")
    print(f"Files included:    {summary['file_count']}")
    print(f"Estimated tokens:  {summary['tokens']:,}")
    if args.skeleton and summary["skeleton_savings_pct"] > 0:
        print(f"Skeleton savings:  ~{summary['skeleton_savings_pct']}% tokens saved!")

    print("\n--- Estimated Input Cost ---")
    for model, cost in summary["costs"].items():
        print(f"  * {model:<18}: ${cost:.5f}")

    # Output destination handling
    if args.output:
        out_path = Path(args.output).resolve()
        out_path.write_text(bundle, encoding="utf-8")
        print(f"\nContext written to: {out_path}")
    elif not args.copy:
        # If no output file and no copy flag, print snippet and guidance
        print("\n(Tip: use -c to copy directly to clipboard, or -o context.md to save to file)")

    if args.copy:
        if copy_to_clipboard(bundle):
            print("\nSuccessfully copied LLM context bundle to clipboard! Ready to paste into ChatGPT/Claude.")
        else:
            print("\nWarning: Could not access system clipboard. Specify -o <filename> to save output.", file=sys.stderr)


if __name__ == "__main__":
    main()
