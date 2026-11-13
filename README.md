# 🧠 code3context (`c2c`)

> **Pack, skeletonize, and optimize any repository into LLM-ready context with token & cost estimates.**

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-brightgreen.svg)](pyproject.toml)
[![Zero Dependency](https://img.shields.io/badge/core-zero--dependency-orange.svg)](#features)
[![Buy Me a Coffee](https://img.shields.io/badge/Buy%20Me%20a%20Coffee-Donate-yellow.svg?logo=buy-me-a-coffee)](https://buymeacoffee.com/carlosdevkadu)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)](CONTRIBUTING.md)

---

## 💖 Support & Sponsor

If **code3context** saved you tokens, time, or API costs on your projects, consider buying me a coffee:

[![Buy Me a Coffee](https://img.shields.io/badge/Buy%20Me%20a%20Coffee-Donate-yellow.svg?style=for-the-badge&logo=buy-me-a-coffee)](https://buymeacoffee.com/carlosdevkadu)

👉 [buymeacoffee.com/carlosdevkadu](https://buymeacoffee.com/carlosdevkadu)

---

## ⚡ Highlights

* 🦴 **Smart Skeleton Mode (`-s`)**: Extracts interfaces, signatures, and docstrings while stripping bodies. Saves ~70–85% of tokens.
* 💰 **Token & Cost Calculator**: Automatically calculates input tokens and estimates API costs across Claude 3.5 Sonnet, GPT-4o, Gemini 1.5 Pro/Flash, and DeepSeek V3.
* 📋 **Direct to Clipboard (`-c`)**: One flag copies the formatted bundle directly to your OS clipboard. Just run `c2c -s -c` and press `Ctrl+V` in ChatGPT or Claude.
* 🛡️ **Zero-Leak Security**: Automatically ignores `.env`, private keys (`*.pem`, `*.key`), credentials, and database files.

---

## 🚀 Quick Start

### 1-Line Usage

```bash
# 1. Pack current folder with Skeleton mode and copy directly to clipboard
python -m cli . -s -c

# 2. Pack a specific directory and save to a markdown file
python -m cli path/to/project -s -o context.md

# 3. Launch the full Web SaaS Dashboard locally
python -m server
```
