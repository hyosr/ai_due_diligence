from jinja2 import Template
import markdown2
from weasyprint import HTML

TEMPLATE = """
# AI Due Diligence Report

- **Company:** {{ company_name }}
- **Website:** {{ website }}
- **Generated at:** {{ generated_at }}
- **Credibility Score:** **{{ score }}/100**
- **Confidence:** **{{ confidence }}%**

## Executive Summary
{{ summary }}

## Explainability (Why this score)
{% for e in explanations %}
### {{ e.key }}
- Weight: {{ e.weight }}
- Normalized value: {{ e.numeric_value }}
- Contribution: {{ e.contribution }}
- Rationale: {{ e.rationale }}
- Rule explanation: {{ e.reason }}

{% endfor %}
"""

def build_markdown_report(company_name, website, score, confidence, summary, explanations, generated_at):
    return Template(TEMPLATE).render(
        company_name=company_name,
        website=website,
        generated_at=generated_at,
        score=score,
        confidence=confidence,
        summary=summary,
        explanations=explanations
    )

def markdown_to_pdf_file(markdown_text: str, output_path: str):
    html_body = markdown2.markdown(markdown_text)
    html = f"""
    <html>
      <head>
        <meta charset="utf-8">
        <style>
          body {{ font-family: Arial, sans-serif; margin: 24px; }}
          h1, h2, h3 {{ color: #222; }}
          p, li {{ font-size: 12px; line-height: 1.45; }}
        </style>
      </head>
      <body>{html_body}</body>
    </html>
    """
    HTML(string=html).write_pdf(output_path)