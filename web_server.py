"""Simple web server for llmstxt-tools web interface."""

import json
import os
import sys
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs

# Add parent to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from llmstxt_tools.core import check_live_llmstxt, generate_from_sitemap


HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>llms.txt Checker & Validator — llmstxt-tools</title>
<meta name="description" content="Free tool to check if a website has an llms.txt file and validate it. The llms.txt standard helps AI systems discover your content.">
<style>
  :root { --bg: #0d1117; --surface: #161b22; --border: #30363d; --text: #e6edf3; --dim: #8b949e; --accent: #58a6ff; --green: #3fb950; --red: #f85149; --radius: 12px; }
  * { margin: 0; padding: 0; box-sizing: border-box; }
  body { font-family: -apple-system,BlinkMacSystemFont,'Segoe UI','Noto Sans',Helvetica,Arial,sans-serif; background: var(--bg); color: var(--text); line-height: 1.6; min-height: 100vh; }
  .container { max-width: 800px; margin: 0 auto; padding: 40px 20px; }
  h1 { font-size: 32px; margin-bottom: 8px; }
  h1 span { color: var(--accent); }
  .subtitle { color: var(--dim); font-size: 15px; margin-bottom: 32px; }
  .card { background: var(--surface); border: 1px solid var(--border); border-radius: var(--radius); padding: 24px; margin-bottom: 20px; }
  input[type=text] { width: 100%; padding: 12px 16px; background: var(--bg); border: 1px solid var(--border); border-radius: 8px; color: var(--text); font-size: 15px; margin-bottom: 12px; }
  input[type=text]:focus { outline: none; border-color: var(--accent); }
  button { padding: 10px 24px; background: var(--accent); color: #000; border: none; border-radius: 8px; font-weight: 600; font-size: 14px; cursor: pointer; }
  button:hover { opacity: .9; }
  button:disabled { opacity: .5; cursor: not-allowed; }
  .result { display: none; }
  .result.visible { display: block; }
  .result-header { display: flex; align-items: center; gap: 12px; margin-bottom: 16px; }
  .pass { color: var(--green); }
  .fail { color: var(--red); }
  .score-ring { width: 60px; height: 60px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-size: 20px; font-weight: 700; flex-shrink: 0; }
  .check-item { padding: 8px 0; display: flex; align-items: flex-start; gap: 8px; font-size: 14px; }
  .check-item .icon { flex-shrink: 0; }
  .check-detail { color: var(--dim); font-size: 13px; }
  .preview { background: #000; border: 1px solid var(--border); border-radius: 8px; padding: 16px; font-family: monospace; font-size: 13px; white-space: pre-wrap; max-height: 300px; overflow: auto; margin-top: 12px; }
  .features { display: grid; grid-template-columns: 1fr 1fr; gap: 16px; margin: 32px 0; }
  .feature { background: var(--surface); border: 1px solid var(--border); border-radius: var(--radius); padding: 20px; }
  .feature h3 { font-size: 16px; margin-bottom: 8px; }
  .feature p { font-size: 14px; color: var(--dim); }
  .pricing { display: grid; grid-template-columns: 1fr 1fr; gap: 16px; margin: 32px 0; }
  .plan { background: var(--surface); border: 1px solid var(--border); border-radius: var(--radius); padding: 24px; }
  .plan.featured { border-color: var(--accent); }
  .plan h3 { font-size: 18px; }
  .plan .price { font-size: 28px; font-weight: 700; margin: 8px 0 16px; }
  .plan ul { list-style: none; margin-bottom: 20px; }
  .plan ul li { padding: 4px 0; font-size: 14px; color: var(--dim); }
  .plan ul li::before { content: "\\2713 "; color: var(--green); }
  .btn { display: inline-block; padding: 10px 20px; border-radius: 8px; font-weight: 600; text-decoration: none; text-align: center; }
  .btn-primary { background: var(--accent); color: #000; }
  .btn-gumroad { background: #ff90e8; color: #000; }
  .footer { text-align: center; padding: 24px; color: var(--dim); font-size: 13px; border-top: 1px solid var(--border); margin-top: 32px; }
  .footer a { color: var(--accent); text-decoration: none; }
  .error { color: var(--red); padding: 12px; background: rgba(248,81,73,.1); border: 1px solid var(--red); border-radius: 8px; margin-bottom: 12px; }
  .loading { text-align: center; padding: 20px; color: var(--dim); }
  .spinner { display: inline-block; width: 20px; height: 20px; border: 2px solid var(--border); border-top-color: var(--accent); border-radius: 50%; animation: spin .8s linear infinite; margin-right: 8px; vertical-align: middle; }
  @keyframes spin { to { transform: rotate(360deg); } }
  @media (max-width: 600px) { .features, .pricing { grid-template-columns: 1fr; } }
  .install-box { background: #000; border: 1px solid var(--border); border-radius: 8px; padding: 16px; font-family: monospace; font-size: 14px; margin: 16px 0; }
</style>
</head>
<body>
<div class="container">
  <h1><span>llms.txt</span> Checker</h1>
  <p class="subtitle">Check if a website has an llms.txt file, validate it against the spec, and get improvement suggestions.</p>

  <div class="card">
    <h3>Check a domain</h3>
    <p style="color:var(--dim);font-size:14px;margin-bottom:12px;">Enter a domain name (e.g., example.com or https://example.com)</p>
    <input type="text" id="domainInput" placeholder="example.com" onkeydown="if(event.key==='Enter') checkDomain()">
    <button id="checkBtn" onclick="checkDomain()">Check llms.txt</button>
    <div id="loading" class="loading" style="display:none;"><span class="spinner"></span> Checking...</div>
    <div id="error" class="error" style="display:none;"></div>
    <div id="result" class="result"></div>
  </div>

  <div class="features">
    <div class="feature"><h3>🔍 Validate</h3><p>Check llms.txt files against the spec. Score, issues, and suggestions included.</p></div>
    <div class="feature"><h3>⚡ Generate</h3><p>Generate an llms.txt from your sitemap. Premium feature — <a href="https://grantshatz.gumroad.com/l/llmstxt-pro" style="color:var(--accent)">get license</a>.</p></div>
    <div class="feature"><h3>📦 CLI Tool</h3><p>Install via pip: <code style="font-size:12px">pip install llmstxt-tools</code></p></div>
    <div class="feature"><h3>🔗 Open Source</h3><p><a href="https://github.com/astra-intelligence/llmstxt-tools" style="color:var(--accent)">GitHub repo</a> — MIT licensed.</p></div>
  </div>

  <div class="pricing">
    <div class="plan">
      <h3>Free</h3>
      <div class="price">$0</div>
      <ul>
        <li>Check any domain's llms.txt</li>
        <li>Validate local files</li>
        <li>JSON output</li>
      </ul>
      <a href="https://github.com/astra-intelligence/llmstxt-tools" class="btn btn-primary" style="width:100%">Install CLI</a>
    </div>
    <div class="plan featured">
      <h3>Premium</h3>
      <div class="price">$1+</div>
      <ul>
        <li>Generate from sitemap</li>
        <li>Custom sections</li>
        <li>Unlimited usage</li>
        <li>Priority support</li>
      </ul>
      <a href="https://grantshatz.gumroad.com/l/llmstxt-pro" class="btn btn-gumroad" style="width:100%">Buy License →</a>
    </div>
  </div>

  <div class="card">
    <h3>Quick Install</h3>
    <div class="install-box">pip install llmstxt-tools</div>
    <p style="color:var(--dim);font-size:14px;">Or install directly from GitHub:</p>
    <div class="install-box">pip install git+https://github.com/astra-intelligence/llmstxt-tools.git</div>
  </div>

  <div class="footer">
    Built by <a href="https://github.com/astra-intelligence">Astra Intelligence Labs</a> · 
    <a href="https://github.com/astra-intelligence/llmstxt-tools">GitHub</a> · 
    <a href="https://grantshatz.gumroad.com/l/llmstxt-pro">Premium</a> · 
    <a href="https://llmstxt.org/">llms.txt Spec</a>
  </div>
</div>

<script>
function showError(msg) {
  var el = document.getElementById('error');
  el.textContent = msg;
  el.style.display = 'block';
}

function showResult(html) {
  var el = document.getElementById('result');
  el.innerHTML = html;
  el.classList.add('visible');
}

async function checkDomain() {
  var domain = document.getElementById('domainInput').value.trim();
  if (!domain) { showError('Enter a domain name'); return; }
  
  document.getElementById('error').style.display = 'none';
  document.getElementById('result').classList.remove('visible');
  document.getElementById('loading').style.display = 'block';
  document.getElementById('checkBtn').disabled = true;
  
  try {
    var resp = await fetch('/api/check?domain=' + encodeURIComponent(domain));
    var data = await resp.json();
    document.getElementById('loading').style.display = 'none';
    document.getElementById('checkBtn').disabled = false;
    
    if (data.error) { showError(data.error); return; }
    
    if (!data.exists) {
      showResult('<div class="result-header"><span class="fail" style="font-size:40px;">&#10007;</span><div><strong>No llms.txt found</strong><br><span style="color:var(--dim)">' + (data.url || '') + '</span><br>HTTP ' + (data.status || 'N/A') + '</div></div>');
      return;
    }
    
    var scoreClass = data.score >= 60 ? 'pass' : 'fail';
    var scoreColor = data.score >= 80 ? '#3fb950' : data.score >= 60 ? '#d29922' : '#f85149';
    var checksHtml = '';
    for (var c of data.checks) {
      var icon = c.pass ? '&#10003;' : '&#10007;';
      var cls = c.pass ? 'pass' : 'fail';
      checksHtml += '<div class="check-item"><span class="icon ' + cls + '">' + icon + '</span><div><strong>' + c.check + '</strong><div class="check-detail">' + c.detail + '</div></div></div>';
    }
    var previewHtml = data.content_preview ? '<div class="preview">' + escapeHtml(data.content_preview) + '</div>' : '';
    
    showResult(
      '<div class="result-header">' +
      '<div class="score-ring" style="border:3px solid ' + scoreColor + ';color:' + scoreColor + '">' + data.score + '</div>' +
      '<div><strong style="font-size:18px">' + data.summary + '</strong><br><span style="color:var(--dim);font-size:13px">' + (data.url || '') + '</span></div>' +
      '</div>' +
      '<div>' + checksHtml + '</div>' +
      (data.score < 100 ? '<p style="margin-top:16px;font-size:13px;color:var(--dim)">Tips: ' + getTip(data) + '</p>' : '') +
      previewHtml
    );
  } catch (e) {
    document.getElementById('loading').style.display = 'none';
    document.getElementById('checkBtn').disabled = false;
    showError('Connection error: ' + e.message);
  }
}

function escapeHtml(text) {
  var div = document.createElement('div');
  div.textContent = text;
  return div.innerHTML;
}

function getTip(data) {
  var tips = [];
  for (var c of data.checks) {
    if (!c.pass) tips.push(c.detail);
  }
  return tips.length ? tips.join('. ') : 'Looks good overall!';
}
</script>
</body>
</html>"""


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path
        
        if path == "/" or path == "/index.html":
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Cache-Control", "no-cache")
            self.end_headers()
            self.wfile.write(HTML_TEMPLATE.encode("utf-8"))
        
        elif path == "/api/check":
            params = parse_qs(parsed.query)
            domain = params.get("domain", [""])[0].strip()
            
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            
            if not domain:
                self.wfile.write(json.dumps({"error": "domain parameter required"}).encode())
                return
            
            result = check_live_llmstxt(domain)
            self.wfile.write(json.dumps(result).encode())
        
        else:
            self.send_response(404)
            self.end_headers()
            self.wfile.write(b"Not found")
    
    def log_message(self, format, *args):
        sys.stderr.write("[%s] %s\n" % (self.log_date_time_string(), format % args))


def main():
    port = int(os.environ.get("PORT", 8083))
    server = HTTPServer(("0.0.0.0", port), Handler)
    print(f"llmstxt-tools web server running on http://0.0.0.0:{port}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down...")


if __name__ == "__main__":
    main()