import re
from django import template
import markdown2
from django.utils.safestring import mark_safe


register = template.Library()


@register.filter
def get_choice(question, letter):
    return getattr(question, f"choice_{letter.lower()}", "")


@register.filter(name="add_class")
def add_class(field, css_class):
    return field.as_widget(attrs={"class": css_class})


@register.filter
def safe_markdown_with_lang(value, category):
    category_to_lang = {
        "sql": "sql",
        "database": "sql",
        "python": "python",
        "html": "html",
        "css": "css",
        "js": "javascript",
        "javascript": "javascript",
        "c": "c",
        "c++": "cpp",
        "java": "java",
        "shell": "bash",
        "bash": "bash",
    }

    # ✅ 防呆
    if not value or not isinstance(value, str):
        return ""

    lang = category_to_lang.get(
        str(category).lower().strip() if category else "", "plaintext"
    )

    # ✅ 自動補 code block（for SQL）
    if "```" not in value and re.search(
        r"\b(SELECT|INSERT|UPDATE|DELETE|FROM|WHERE|JOIN|INNER|LEFT|RIGHT|FULL|OUTER|ON|GROUP BY|ORDER BY|HAVING|AS|AND|OR|NOT|IN|IS|NULL|VALUES|SET|CREATE|ALTER|DROP|TABLE|VIEW|INDEX|DATABASE|UNION|ALL|DISTINCT|LIMIT|OFFSET|CASE|WHEN|THEN|ELSE|END)\b",
        value,
        re.IGNORECASE,
    ):
        value = f"```{lang}\n{value.strip()}\n```"

    # ✅ 轉換為 HTML
    html = markdown2.markdown(value, extras=["fenced-code-blocks", "tables"])
    html = html.replace("<code>", f'<code class="language-{lang}">')

    return mark_safe(html)


@register.filter
def safe_markdown_with_lang_for_options(text, category):
    import markdown2
    import re

    category_to_lang = {
        "database": "sql",
        "sql": "sql",
        "python": "python",
        "html": "html",
        "css": "css",
        "js": "javascript",
        "javascript": "javascript",
        "c": "c",
        "c++": "cpp",
        "java": "java",
        "shell": "bash",
        "bash": "bash",
    }

    # ✅ 防呆處理 category 為 None 的情況
    category = str(category or "").lower()
    lang = category_to_lang.get(category, "plaintext")

    def wrap_code(match):
        code = match.group(1)
        return f"\n```{lang}\n{code}\n```\n"

    if text:
        text = re.sub(r"`([^`]+)`", wrap_code, text)

    html = markdown2.markdown(text.strip(), extras=["fenced-code-blocks", "tables"])
    return mark_safe(html)


@register.filter
@register.filter
def safe_markdown_ai(text):
    import markdown2
    from django.utils.safestring import mark_safe
    import re
    from opencc import OpenCC

    if not text or not isinstance(text, str):
        return ""

    # Step 1：簡轉繁
    cc = OpenCC("s2t")
    text = cc.convert(text)

    # Step 2：清理 markdown 標題
    cleaned = re.sub(r"(?m)^(\#{1,6})(\S)", r"\1 \2", text.strip())

    # Step 3：Markdown 轉 HTML
    html = markdown2.markdown(cleaned, extras=["fenced-code-blocks", "tables"])

    # Step 4：補上預設語言 class
    html = re.sub(r"<pre><code>", '<pre><code class="language-plaintext">', html)

    return mark_safe(html)


@register.filter
def float_to_percent(value):
    try:
        return f"{float(value) * 100:.0f}%"
    except (ValueError, TypeError):
        return "0%"


@register.filter
def div(value, arg):
    try:
        return float(value) / float(arg)
    except (ValueError, ZeroDivisionError):
        return 0


@register.filter
def mul(value, arg):
    try:
        return float(value) * float(arg)
    except (ValueError, TypeError):
        return 0


@register.filter
def dict_get(d, key):
    if d is None:
        return ""
    return d.get(key, "")
