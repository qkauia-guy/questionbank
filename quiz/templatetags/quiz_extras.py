import re
from django import template
import markdown2

register = template.Library()


@register.filter
def get_choice(question, letter):
    return getattr(question, f"choice_{letter.lower()}", "")


@register.filter
def safe_markdown_no_h1(value):
    # 把開頭的 # 標題替換為純文字顯示（不轉成 <h1> 等 HTML 標題）
    cleaned = re.sub(
        r"(?m)^(\#{1,6})\s*", r"\1 ", value
    )  # 保留 #，去除 markdown 標題語法作用
    html = markdown2.markdown(cleaned, extras=["fenced-code-blocks", "tables"])
    html = html.replace("<code>", '<code class="language-python">')
    return html


@register.filter(name="add_class")
def add_class(field, css_class):
    return field.as_widget(attrs={"class": css_class})
