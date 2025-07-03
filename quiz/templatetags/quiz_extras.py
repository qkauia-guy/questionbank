import re
from django import template
import markdown2

register = template.Library()


@register.filter
def get_choice(question, letter):
    return getattr(question, f"choice_{letter.lower()}", "")


@register.filter
def safe_markdown_no_h1(value):
    cleaned = re.sub(r"(?m)^#+\s?", "// ", value)
    html = markdown2.markdown(cleaned, extras=["fenced-code-blocks", "tables"])
    html = html.replace("<code>", '<code class="language-python">')
    return html


@register.filter(name="add_class")
def add_class(field, css_class):
    return field.as_widget(attrs={"class": css_class})
