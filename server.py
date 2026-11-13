"""
Zero-dependency SaaS Web App & API Server for code2context.
Run with: python -m code2context.server
"""

import os
import sys
import json
import tempfile
import urllib.parse
from http.server import HTTPServer, BaseHTTPRequestHandler
from pathlib import Path

from . import __version__
from .core import pack_codebase
from .skeleton import extract_skeleton
from .tokenizer import estimate_tokens, estimate_costs

HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="en" class="dark">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>code2context Pro - LLM Context Packer & Token Optimizer</title>
  <script src="https://cdn.tailwindcss.com"></script>
  <script>
    tailwind.config = {
      darkMode: 'class',
      theme: {
        extend: {
          colors: {
            brand: { 500: '#6366f1', 600: '#4f46e5', 700: '#4338ca' }
          }
        }
      }
    }
  </script>
  <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
  <style>
    body { background-color: #0b0f19; color: #f3f4f6; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; }
    .glass { background: rgba(17, 24, 39, 0.7); backdrop-filter: blur(12px); border: 1px solid rgba(255, 255, 255, 0.08); }
    .gradient-text { background: linear-gradient(135deg, #a5b4fc 0%, #6366f1 50%, #ec4899 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }
  </style>
</head>
<body class="min-h-screen flex flex-col">

  <!-- Header -->
  <header class="border-b border-gray-800 glass sticky top-0 z-50">
    <div class="max-w-7xl mx-auto px-4 h-16 flex items-center justify-between">
      <div class="flex items-center space-x-3">
        <div class="w-9 h-9 rounded-xl bg-gradient-to-tr from-brand-600 to-pink-500 flex items-center justify-center font-bold text-white shadow-lg shadow-brand-500/20">
          <i class="fa-solid fa-brain"></i>
        </div>
        <span class="font-bold text-xl tracking-tight">code2context <span class="text-xs bg-brand-500/20 text-brand-400 border border-brand-500/30 px-2 py-0.5 rounded-full ml-1">SaaS Pro</span></span>
      </div>
      <div class="flex items-center space-x-4">
        <a href="#pricing" class="text-sm text-gray-300 hover:text-white transition">Pricing</a>
        <a href="#api" class="text-sm text-gray-300 hover:text-white transition">API Docs</a>
        <button onclick="openCheckout('Pro', 9)" class="bg-brand-600 hover:bg-brand-500 text-white text-sm font-semibold px-4 py-2 rounded-lg shadow-lg shadow-brand-600/30 transition">
          Upgrade to Pro ($9/mo)
        </button>
      </div>
    </div>
  </header>

  <!-- Hero & Main App -->
  <main class="flex-1 max-w-7xl mx-auto px-4 py-10 w-full space-y-12">
    
    <div class="text-center space-y-3 max-w-3xl mx-auto">
      <h1 class="text-4xl sm:text-5xl font-extrabold tracking-tight">
        Pack any Codebase into <span class="gradient-text">LLM Context</span>
      </h1>
      <p class="text-gray-400 text-base sm:text-lg">
        Smart skeletonization removes implementation fluff while keeping 100% of architectural signatures. Save up to 80% on API tokens.
      </p>
    </div>

    <!-- Interactive Tool Card -->
    <div class="grid grid-cols-1 lg:grid-cols-12 gap-8">
      
      <!-- Left Panel: Input & Controls -->
      <div class="lg:col-span-5 space-y-6">
        <div class="glass rounded-2xl p-6 space-y-5">
          <h2 class="text-lg font-semibold flex items-center gap-2">
            <i class="fa-solid fa-sliders text-brand-400"></i> Settings & Code Input
          </h2>

          <!-- Mode Toggles -->
          <div class="space-y-3 bg-gray-900/60 p-4 rounded-xl border border-gray-800">
            <div class="flex items-center justify-between">
              <div>
                <span class="text-sm font-medium">Smart Skeleton Mode</span>
                <p class="text-xs text-gray-400">Omit function bodies, keep signatures & docstrings</p>
              </div>
              <input type="checkbox" id="skeletonToggle" checked class="w-5 h-5 accent-brand-600 rounded cursor-pointer">
            </div>
            
            <div class="flex items-center justify-between pt-2 border-t border-gray-800/80">
              <span class="text-sm font-medium">Format</span>
              <select id="formatSelect" class="bg-gray-800 text-sm border border-gray-700 rounded-lg px-2.5 py-1 text-gray-200 focus:outline-none focus:border-brand-500">
                <option value="markdown">Markdown (ChatGPT / Gemini)</option>
                <option value="xml">XML (Claude / Anthropic)</option>
              </select>
            </div>
          </div>

          <!-- Code Snippet / Paste Box -->
          <div>
            <label class="block text-xs font-semibold uppercase text-gray-400 mb-1.5">Paste Code or File Content</label>
            <textarea id="codeInput" rows="8" class="w-full bg-gray-900 border border-gray-800 rounded-xl p-3 text-xs font-mono text-gray-200 focus:outline-none focus:border-brand-500" placeholder="Paste your Python/TypeScript/Go code here, or click 'Load Demo'..."></textarea>
          </div>

          <div class="flex items-center gap-3">
            <button onclick="processCode()" class="flex-1 bg-gradient-to-r from-brand-600 to-pink-600 hover:opacity-95 text-white font-semibold py-2.5 rounded-xl text-sm shadow-lg shadow-brand-500/20 transition flex items-center justify-center gap-2">
              <i class="fa-solid fa-wand-magic-sparkles"></i> Optimize & Estimate Cost
            </button>
            <button onclick="loadDemo()" class="bg-gray-800 hover:bg-gray-700 text-xs px-3 py-2.5 rounded-xl border border-gray-700 transition">
              Load Demo
            </button>
          </div>
        </div>

        <!-- Token Savings Metric Widget -->
        <div class="glass rounded-2xl p-6 bg-gradient-to-br from-brand-950/40 to-gray-900 border border-brand-500/20">
          <div class="flex items-center justify-between mb-4">
            <span class="text-xs uppercase tracking-wider font-semibold text-brand-400">Token Cost Economy</span>
            <span id="savingsBadge" class="bg-emerald-500/20 text-emerald-400 text-xs font-bold px-2 py-0.5 rounded-full border border-emerald-500/30">
              -78% Tokens
            </span>
          </div>
          <div class="grid grid-cols-2 gap-4">
            <div class="bg-gray-900/60 p-3 rounded-xl border border-gray-800">
              <span class="text-xs text-gray-400 block">Original Tokens</span>
              <span id="origTokens" class="text-lg font-bold text-gray-300">4,200</span>
            </div>
            <div class="bg-brand-900/30 p-3 rounded-xl border border-brand-500/30">
              <span class="text-xs text-brand-300 block">Optimized Tokens</span>
              <span id="optTokens" class="text-lg font-bold text-emerald-400">920</span>
            </div>
          </div>
          <div class="mt-4 pt-3 border-t border-gray-800 text-xs text-gray-400 flex justify-between">
            <span>Estimated Claude 3.5 Cost:</span>
            <span id="costDisplay" class="font-bold text-gray-200">$0.00276</span>
          </div>
        </div>
      </div>

      <!-- Right Panel: Result & Copy -->
      <div class="lg:col-span-7 flex flex-col space-y-4">
        <div class="glass rounded-2xl p-6 flex-1 flex flex-col space-y-3">
          <div class="flex items-center justify-between pb-3 border-b border-gray-800">
            <h3 class="font-semibold text-sm flex items-center gap-2">
              <i class="fa-solid fa-code text-pink-400"></i> Optimized Context Output
            </h3>
            <button onclick="copyResult()" id="copyBtn" class="bg-brand-600 hover:bg-brand-500 text-white text-xs font-semibold px-3 py-1.5 rounded-lg flex items-center gap-1.5 transition">
              <i class="fa-regular fa-copy"></i> Copy to Clipboard
            </button>
          </div>
          <textarea id="resultOutput" readonly rows="18" class="flex-1 w-full bg-gray-950 border border-gray-800/80 rounded-xl p-3 text-xs font-mono text-gray-300 focus:outline-none resize-none"></textarea>
        </div>
      </div>

    </div>

    <!-- Pricing Section (How You Make Money) -->
    <section id="pricing" class="py-12 border-t border-gray-800 space-y-8">
      <div class="text-center max-w-2xl mx-auto space-y-2">
        <h2 class="text-3xl font-extrabold tracking-tight">Simple, Transparent Pricing</h2>
        <p class="text-gray-400 text-sm">Monetize your code2context deployment with built-in subscription tiers.</p>
      </div>

      <div class="grid grid-cols-1 md:grid-cols-3 gap-6 max-w-5xl mx-auto">
        
        <!-- Free Tier -->
        <div class="glass rounded-2xl p-6 space-y-5 border border-gray-800">
          <div>
            <h3 class="font-bold text-lg">Community Free</h3>
            <p class="text-xs text-gray-400">For individual hobbyists</p>
          </div>
          <div class="text-3xl font-extrabold">$0 <span class="text-xs font-normal text-gray-400">/ forever</span></div>
          <ul class="text-xs space-y-2.5 text-gray-300">
            <li><i class="fa-solid fa-check text-emerald-400 mr-2"></i> CLI Tool access</li>
            <li><i class="fa-solid fa-check text-emerald-400 mr-2"></i> Basic token estimation</li>
            <li><i class="fa-solid fa-check text-emerald-400 mr-2"></i> Up to 20 files per run</li>
          </ul>
          <button class="w-full bg-gray-800 hover:bg-gray-700 text-xs font-semibold py-2.5 rounded-xl transition">
            Current Plan
          </button>
        </div>

        <!-- Pro Tier (Most Popular) -->
        <div class="glass rounded-2xl p-6 space-y-5 border-2 border-brand-500 relative shadow-2xl shadow-brand-500/20">
          <span class="absolute -top-3 left-1/2 -translate-x-1/2 bg-gradient-to-r from-brand-600 to-pink-600 text-white text-[10px] uppercase font-extrabold px-3 py-0.5 rounded-full">
            Most Popular
          </span>
          <div>
            <h3 class="font-bold text-lg text-white">Developer Pro</h3>
            <p class="text-xs text-gray-400">For active AI engineers & builders</p>
          </div>
          <div class="text-3xl font-extrabold text-white">$9 <span class="text-xs font-normal text-gray-400">/ month</span></div>
          <ul class="text-xs space-y-2.5 text-gray-200">
            <li><i class="fa-solid fa-check text-emerald-400 mr-2"></i> Unlimited repository size</li>
            <li><i class="fa-solid fa-check text-emerald-400 mr-2"></i> Smart AST Skeletonizer (all languages)</li>
            <li><i class="fa-solid fa-check text-emerald-400 mr-2"></i> Web Dashboard & Cloud Export</li>
            <li><i class="fa-solid fa-check text-emerald-400 mr-2"></i> 1-Click Clipboard integration</li>
          </ul>
          <button onclick="openCheckout('Pro', 9)" class="w-full bg-gradient-to-r from-brand-600 to-pink-600 hover:opacity-95 text-white text-xs font-bold py-2.5 rounded-xl shadow-lg shadow-brand-500/30 transition">
            Upgrade to Pro ($9/mo)
          </button>
        </div>

        <!-- API / Enterprise Tier -->
        <div class="glass rounded-2xl p-6 space-y-5 border border-gray-800">
          <div>
            <h3 class="font-bold text-lg">Team & B2B API</h3>
            <p class="text-xs text-gray-400">For teams building AI agents</p>
          </div>
          <div class="text-3xl font-extrabold">$29 <span class="text-xs font-normal text-gray-400">/ month</span></div>
          <ul class="text-xs space-y-2.5 text-gray-300">
            <li><i class="fa-solid fa-check text-emerald-400 mr-2"></i> High-speed REST API endpoint</li>
            <li><i class="fa-solid fa-check text-emerald-400 mr-2"></i> Automated CI/CD integration</li>
            <li><i class="fa-solid fa-check text-emerald-400 mr-2"></i> Custom secret filtering rules</li>
            <li><i class="fa-solid fa-check text-emerald-400 mr-2"></i> Priority support</li>
          </ul>
          <button onclick="openCheckout('Team & API', 29)" class="w-full bg-gray-800 hover:bg-gray-700 text-xs font-semibold py-2.5 rounded-xl transition">
            Get API Access ($29/mo)
          </button>
        </div>

      </div>
    </section>

    <!-- B2B API Section -->
    <section id="api" class="py-8 border-t border-gray-800 space-y-4">
      <h3 class="text-xl font-bold flex items-center gap-2">
        <i class="fa-solid fa-terminal text-brand-400"></i> B2B API Integration Endpoint
      </h3>
      <p class="text-xs text-gray-400">Companies can integrate your endpoint directly into their LLM pipelines:</p>
      <pre class="bg-gray-950 p-4 rounded-xl text-xs font-mono text-emerald-400 border border-gray-800 overflow-x-auto">
curl -X POST http://localhost:8080/api/optimize \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer c2c_live_sample_key" \
  -d '{"code": "def process(): ...", "skeleton": true, "format": "markdown"}'
      </pre>
    </section>

  </main>

  <!-- Checkout Modal -->
  <div id="checkoutModal" class="fixed inset-0 bg-black/80 backdrop-blur-sm z-50 hidden flex items-center justify-center p-4">
    <div class="glass max-w-md w-full rounded-2xl p-6 space-y-5 border border-brand-500/40">
      <div class="flex items-center justify-between pb-3 border-b border-gray-800">
        <h4 class="font-bold text-lg" id="modalPlanTitle">Subscribe to Pro Plan</h4>
        <button onclick="closeCheckout()" class="text-gray-400 hover:text-white">&times;</button>
      </div>
      <p class="text-xs text-gray-300">
        Ready to connect with <b>Stripe</b> or <b>LemonSqueezy</b>. Enter your customer email to generate your Pro API key:
      </p>
      <div class="space-y-3">
        <input type="email" id="customerEmail" placeholder="you@company.com" class="w-full bg-gray-900 border border-gray-700 rounded-xl px-3 py-2 text-sm focus:outline-none focus:border-brand-500">
        <button onclick="confirmSubscription()" class="w-full bg-brand-600 hover:bg-brand-500 text-white font-semibold py-2.5 rounded-xl text-sm transition">
          Generate Pro License Key
        </button>
      </div>
      <div id="keyBox" class="hidden p-3 bg-gray-900 rounded-xl border border-emerald-500/40 text-xs space-y-1">
        <span class="text-emerald-400 font-bold block">✓ License Generated:</span>
        <code id="generatedKey" class="text-gray-200 break-all select-all font-mono"></code>
      </div>
    </div>
  </div>

  <footer class="border-t border-gray-900 py-6 text-center text-xs text-gray-500">
    code2context SaaS v1.0.0 &copy; 2026. Ready for commercial deployment on Railway/Render/Vercel.
  </footer>

  <script>
    const DEMO_CODE = `import os
import sys
from typing import List, Dict

class NeuralPipeline:
    # Processes batch inference across multimodal inputs
    def __init__(self, model_id: str, batch_size: int = 32):
        self.model_id = model_id
        self.batch_size = batch_size
        self._weights = None

    def load_weights(self, path: str) -> bool:
        # Loads model tensor weights from disk
        data = open(path, "rb").read()
        self._weights = [float(x) for x in range(1000)]
        return True

    def run_inference(self, inputs: List[str]) -> Dict[str, float]:
        # Runs heavy matrix multiplication on input vectors
        scores = {}
        for item in inputs:
            tokens = item.split()
            score = sum(len(t) for t in tokens) * 1.414
            scores[item] = score
        return scores
`;

    function loadDemo() {
      document.getElementById('codeInput').value = DEMO_CODE;
      processCode();
    }

    async function processCode() {
      const code = document.getElementById('codeInput').value;
      const skeleton = document.getElementById('skeletonToggle').checked;
      const format = document.getElementById('formatSelect').value;

      if (!code.trim()) {
        loadDemo();
        return;
      }

      const res = await fetch('/api/optimize', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ code, skeleton, format })
      });

      const data = await res.json();
      document.getElementById('resultOutput').value = data.bundle;
      document.getElementById('origTokens').innerText = data.orig_tokens.toLocaleString();
      document.getElementById('optTokens').innerText = data.opt_tokens.toLocaleString();
      document.getElementById('savingsBadge').innerText = '-' + data.savings_pct + '% Tokens';
      document.getElementById('costDisplay').innerText = '$' + data.claude_cost.toFixed(5);
    }

    function copyResult() {
      const textarea = document.getElementById('resultOutput');
      textarea.select();
      navigator.clipboard.writeText(textarea.value);
      const btn = document.getElementById('copyBtn');
      btn.innerHTML = '<i class="fa-solid fa-check"></i> Copied!';
      setTimeout(() => {
        btn.innerHTML = '<i class="fa-regular fa-copy"></i> Copy to Clipboard';
      }, 2000);
    }

    function openCheckout(plan, price) {
      document.getElementById('modalPlanTitle').innerText = 'Subscribe to ' + plan + ' ($' + price + '/mo)';
      document.getElementById('checkoutModal').classList.remove('hidden');
    }

    function closeCheckout() {
      document.getElementById('checkoutModal').classList.add('hidden');
    }

    function confirmSubscription() {
      const email = document.getElementById('customerEmail').value;
      if (!email) return alert('Please enter an email.');
      const key = 'c2c_live_' + btoa(email + '_' + Date.now()).replace(/=/g, '');
      document.getElementById('generatedKey').innerText = key;
      document.getElementById('keyBox').classList.remove('hidden');
    }

    // Auto load demo on start
    window.onload = loadDemo;
  </script>
</body>
</html>
"""


class SaaSHandler(BaseHTTPRequestHandler):
    def _send_cors(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization")

    def do_OPTIONS(self):
        self.send_response(200)
        self._send_cors()
        self.end_headers()

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        if parsed.path in ["/", "/index.html"]:
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self._send_cors()
            self.end_headers()
            self.wfile.write(HTML_TEMPLATE.encode("utf-8"))
        elif parsed.path == "/api/health":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self._send_cors()
            self.end_headers()
            self.wfile.write(json.dumps({"status": "healthy", "version": __version__}).encode("utf-8"))
        else:
            self.send_response(404)
            self.end_headers()

    def do_POST(self):
        parsed = urllib.parse.urlparse(self.path)
        if parsed.path == "/api/optimize":
            content_length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(content_length).decode("utf-8")
            try:
                payload = json.loads(body)
            except Exception:
                payload = {}

            code = payload.get("code", "")
            use_skeleton = payload.get("skeleton", True)
            out_format = payload.get("format", "markdown")

            orig_tokens = estimate_tokens(code)
            final_code = extract_skeleton(code, "input.py") if use_skeleton else code
            opt_tokens = estimate_tokens(final_code)

            savings_pct = 0.0
            if orig_tokens > 0:
                savings_pct = round((1 - (opt_tokens / orig_tokens)) * 100, 1)

            costs = estimate_costs(opt_tokens)

            if out_format == "xml":
                bundle = f"<document path=\"snippet.py\">\n  <source_code>\n{final_code}\n  </source_code>\n</document>"
            else:
                bundle = f"### `snippet.py`\n```python\n{final_code}\n```"

            response_data = {
                "bundle": bundle,
                "orig_tokens": orig_tokens,
                "opt_tokens": opt_tokens,
                "savings_pct": max(0.0, savings_pct),
                "claude_cost": costs.get("Claude 3.5 Sonnet", 0.0),
                "all_costs": costs,
            }

            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self._send_cors()
            self.end_headers()
            self.wfile.write(json.dumps(response_data).encode("utf-8"))
        else:
            self.send_response(404)
            self.end_headers()


def start_server(host: str = "127.0.0.1", port: int = 8080):
    server = HTTPServer((host, port), SaaSHandler)
    print(f"\n[code2context SaaS Server Started]")
    print(f"  -> Local Dashboard: http://{host}:{port}")
    print(f"  -> Public API:       http://{host}:{port}/api/optimize")
    print(f"  -> Pricing & Checkout live on landing page")
    print("Press Ctrl+C to stop.\n")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping server...")
        server.server_close()


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    start_server(port=port)
