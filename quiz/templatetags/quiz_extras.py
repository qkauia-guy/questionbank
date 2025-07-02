from django import template
import markdown2

register = template.Library()


@register.filter
def get_choice(question, letter):
    return getattr(question, f"choice_{letter.lower()}", "")


@register.filter
def safe_markdown_no_h1(value):
    # Markdown 轉 HTML，支援表格與程式區塊
    html = markdown2.markdown(value, extras=["fenced-code-blocks", "tables"])

    # 讓 code 區塊自動加上 class（例如語法高亮使用）
    html = html.replace("<code>", '<code class="language-python">')

    return html
