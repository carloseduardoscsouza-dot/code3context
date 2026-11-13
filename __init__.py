"""
code2context - Smart Codebase to LLM Context Packer
Pack, skeletonize, and optimize any repository into LLM-ready context with token & cost estimates.
"""

__version__ = "1.0.0"
__author__ = "Open Source Contributor"

from .core import pack_codebase, scan_directory
from .skeleton import extract_skeleton
from .tokenizer import estimate_tokens, estimate_costs

__all__ = [
    "pack_codebase",
    "scan_directory",
    "extract_skeleton",
    "estimate_tokens",
    "estimate_costs",
]
