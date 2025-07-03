import re
from django import template
import markdown2

register = template.Library()


@register.filter
def get_choice(question, letter):
    return getattr(question, f"choice_{letter.lower()}", "")


@register.filter  # ← ✅ 加這行
def safe_markdown_no_h1(value):
    # 把開頭是 # 的行替換成註解，避免變成 <h1>
    cleaned = re.sub(r"(?m)^#+\s?", "// ", value)

    html = markdown2.markdown(cleaned, extras=["fenced-code-blocks", "tables"])
    html = html.replace("<code>", '<code class="language-python">')
    return html
