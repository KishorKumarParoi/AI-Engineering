import os
import re

def build_html():
    handbook_path = os.path.join(os.path.dirname(__file__), '..', 'docs', 'PRINCIPAL_ENGINEER_HANDBOOK.md')
    output_path = os.path.join(os.path.dirname(__file__), '..', 'docs', 'handbook_preview.html')
    
    with open(handbook_path, 'r', encoding='utf-8') as f:
        md_content = f.read()

    # Try importing markdown or fallback to simple parser
    try:
        import markdown
        # Convert ```mermaid ... ``` to <pre class="mermaid">...</pre>
        pattern = re.compile(r'```mermaid\s*\n(.*?)\n```', re.DOTALL)
        processed_md = pattern.sub(r'<pre class="mermaid">\n\1\n</pre>', md_content)
        html_body = markdown.markdown(processed_md, extensions=['extra', 'tables', 'fenced_code'])
    except ImportError:
        # If markdown package not available, embed raw markdown with marked.js in browser
        html_body = f"<div id='raw-md' style='display:none;'>{md_content}</div>"

    html_template = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Zomato Enterprise AI Platform - Principal Architecture Handbook</title>
  <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/github-markdown-css@5/github-markdown-dark.min.css">
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com">
  <link href="https://fonts.googleapis.com/css2?family=Fira+Code:wght@400;600&family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
  <style>
    :root {{
      --bg: #0d1117;
      --card-bg: #161b22;
      --accent: #e23744;
      --border: #30363d;
    }}
    body {{
      background-color: var(--bg);
      color: #c9d1d9;
      font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
      margin: 0;
      padding: 0;
    }}
    .header-bar {{
      position: sticky;
      top: 0;
      z-index: 100;
      background: rgba(22, 27, 34, 0.92);
      backdrop-filter: blur(12px);
      border-bottom: 1px solid var(--border);
      padding: 14px 32px;
      display: flex;
      justify-content: space-between;
      align-items: center;
    }}
    .header-title {{
      font-weight: 700;
      font-size: 16px;
      color: #fff;
      display: flex;
      align-items: center;
      gap: 12px;
    }}
    .badge {{
      background: #e23744;
      color: #fff;
      font-size: 11px;
      font-weight: 700;
      padding: 3px 10px;
      border-radius: 9999px;
      letter-spacing: 0.5px;
    }}
    .container {{
      max-width: 1120px;
      margin: 40px auto;
      padding: 0 24px 80px 24px;
    }}
    .markdown-body {{
      background: transparent !important;
      font-family: inherit !important;
      font-size: 15px;
      line-height: 1.7;
    }}
    .markdown-body pre {{
      background-color: #161b22 !important;
      border: 1px solid var(--border);
      border-radius: 8px;
    }}
    .markdown-body code {{
      font-family: 'Fira Code', monospace !important;
    }}
    pre.mermaid {{
      background: #13171f !important;
      border: 1px solid #388bfd55 !important;
      border-radius: 12px !important;
      padding: 24px !important;
      margin: 28px 0 !important;
      display: flex;
      justify-content: center;
      overflow-x: auto;
    }}
    details {{
      background: #161b22;
      border: 1px solid var(--border);
      border-radius: 8px;
      padding: 14px 18px;
      margin: 20px 0;
    }}
    summary {{
      cursor: pointer;
      font-weight: 600;
      color: #58a6ff;
    }}
  </style>
  <script type="module">
    import mermaid from 'https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.esm.min.mjs';
    mermaid.initialize({{
      startOnLoad: true,
      theme: 'dark',
      themeVariables: {{
        darkMode: true,
        background: '#13171f',
        primaryColor: '#1f6feb',
        primaryTextColor: '#f0f6fc',
        primaryBorderColor: '#388bfd',
        lineColor: '#58a6ff',
        secondaryColor: '#238636',
        tertiaryColor: '#e23744'
      }}
    }});
  </script>
</head>
<body>
  <div class="header-bar">
    <div class="header-title">
      <span>ZOMATO ENTERPRISE PLATFORM</span>
      <span class="badge">PRINCIPAL ARCHITECT HANDBOOK</span>
    </div>
    <div style="font-size: 13px; color: #8b949e;">
      Live Interactive Architecture & System Design
    </div>
  </div>

  <div class="container">
    <article class="markdown-body">
      {html_body}
    </article>
  </div>
</body>
</html>
"""
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html_template)
    print(f"Successfully generated {output_path}")

if __name__ == '__main__':
    build_html()
