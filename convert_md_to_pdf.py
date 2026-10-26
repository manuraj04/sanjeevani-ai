import os
import subprocess
import markdown

md_path = os.path.abspath("PRODUCTION_DEPLOYMENT_GUIDE.md")
html_path = os.path.abspath("PRODUCTION_DEPLOYMENT_GUIDE.html")
pdf_path = os.path.abspath("PRODUCTION_DEPLOYMENT_GUIDE.pdf")

with open(md_path, "r", encoding="utf-8") as f:
    md_content = f.read()

# Convert markdown to HTML with tables, fenced code blocks, and attributes
html_body = markdown.markdown(md_content, extensions=['tables', 'fenced_code', 'nl2br'])

html_template = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>Sanjeevani Scan AI — Production Deployment Guide</title>
<style>
  @page {{
    size: A4;
    margin: 18mm 15mm 18mm 15mm;
    @bottom-right {{
      content: counter(page);
    }}
  }}
  body {{
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
    color: #2D3748;
    line-height: 1.6;
    font-size: 13.5px;
    padding: 0;
    margin: 0;
  }}
  h1 {{
    color: #1B5E20;
    font-size: 26px;
    border-bottom: 2.5px solid #2E7D32;
    padding-bottom: 8px;
    margin-top: 0;
    margin-bottom: 12px;
  }}
  h2 {{
    color: #2E7D32;
    font-size: 19px;
    border-bottom: 1.5px solid #E2E8F0;
    padding-bottom: 6px;
    margin-top: 24px;
    margin-bottom: 10px;
    page-break-after: avoid;
  }}
  h3 {{
    color: #1A365D;
    font-size: 15px;
    margin-top: 18px;
    margin-bottom: 6px;
    page-break-after: avoid;
  }}
  blockquote {{
    background: #F1F8E9;
    border-left: 4px solid #43A047;
    margin: 12px 0;
    padding: 10px 16px;
    border-radius: 4px;
    color: #2E7D32;
    font-weight: 500;
  }}
  table {{
    width: 100%;
    border-collapse: collapse;
    margin: 14px 0;
    font-size: 12.5px;
    page-break-inside: avoid;
  }}
  th, td {{
    border: 1px solid #CBD5E0;
    padding: 8px 12px;
    text-align: left;
  }}
  th {{
    background-color: #E8F5E9;
    color: #1B5E20;
    font-weight: 700;
  }}
  tr:nth-child(even) {{
    background-color: #F7FAFC;
  }}
  pre {{
    background-color: #1A202C;
    color: #E2E8F0;
    padding: 12px;
    border-radius: 6px;
    overflow-x: auto;
    font-family: Consolas, "Fira Code", Monaco, monospace;
    font-size: 12px;
    line-height: 1.45;
    margin: 10px 0;
    page-break-inside: avoid;
  }}
  code {{
    background-color: #EDF2F7;
    color: #C53030;
    padding: 2px 5px;
    border-radius: 4px;
    font-family: Consolas, Monaco, monospace;
    font-size: 12px;
  }}
  pre code {{
    background-color: transparent;
    color: inherit;
    padding: 0;
  }}
  ul, ol {{
    margin: 8px 0;
    padding-left: 22px;
  }}
  li {{
    margin-bottom: 4px;
  }}
  hr {{
    border: none;
    border-top: 1px solid #E2E8F0;
    margin: 20px 0;
  }}
  .badge {{
    display: inline-block;
    padding: 3px 8px;
    border-radius: 12px;
    font-size: 11px;
    font-weight: 600;
  }}
</style>
</head>
<body>
{html_body}
</body>
</html>
"""

with open(html_path, "w", encoding="utf-8") as f:
    f.write(html_template)

print(f"Rendered intermediate HTML at: {html_path}")

# Detect Edge binary path
edge_paths = [
    r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
    r"C:\Program Files\Microsoft\Edge\Application\msedge.exe"
]

edge_bin = None
for p in edge_paths:
    if os.path.exists(p):
        edge_bin = p
        break

if not edge_bin:
    raise FileNotFoundError("Microsoft Edge executable not found for PDF rendering.")

cmd = [
    edge_bin,
    "--headless",
    "--disable-gpu",
    f"--print-to-pdf={pdf_path}",
    f"file:///{html_path.replace(os.sep, '/')}"
]

print(f"Executing: {' '.join(cmd)}")
result = subprocess.run(cmd, capture_output=True, text=True)

if os.path.exists(pdf_path) and os.path.getsize(pdf_path) > 0:
    print(f"SUCCESS: PDF created successfully at {pdf_path} (Size: {os.path.getsize(pdf_path)} bytes)")
else:
    print(f"ERROR: PDF was not created. Stderr: {result.stderr}")
