import re
import markdown2
from django import template
from django.utils.safestring import mark_safe

register = template.Library()


# ------------------ 題目選項與樣式 ------------------


@register.filter
def get_choice(question, letter):
    return getattr(question, f"choice_{letter.lower()}", "")


@register.filter(name="add_class")
def add_class(field, css_class):
    return field.as_widget(attrs={"class": css_class})


# ------------------ 題目說明 markdown ------------------


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

    if not value or not isinstance(value, str):
        return ""

    lang = category_to_lang.get(
        str(category).lower().strip() if category else "", "plaintext"
    )

    if "```" not in value and re.search(
        r"\b(SELECT|INSERT|UPDATE|DELETE|FROM|WHERE|JOIN|GROUP BY|ORDER BY|HAVING|AS|AND|OR|NOT|IN|IS|NULL|VALUES|SET|CREATE|DROP|TABLE|VIEW|LIMIT|OFFSET|CASE)\b",
        value,
        re.IGNORECASE,
    ):
        value = f"```{lang}\n{value.strip()}\n```"

    html = markdown2.markdown(value, extras=["fenced-code-blocks", "tables"])
    html = html.replace("<code>", f'<code class="language-{lang}">')

    return mark_safe(html)


@register.filter
def safe_markdown_with_lang_for_options(text, category):
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
def safe_markdown_ai(text):
    from opencc import OpenCC

    if not text or not isinstance(text, str):
        return ""

    cc = OpenCC("s2t")
    text = cc.convert(text)
    cleaned = re.sub(r"(?m)^(\#{1,6})(\S)", r"\1 \2", text.strip())

    html = markdown2.markdown(cleaned, extras=["fenced-code-blocks", "tables"])
    html = re.sub(r"<pre><code>", '<pre><code class="language-plaintext">', html)

    return mark_safe(html)


# ------------------ 計算與資料取得 ------------------


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


# ------------------ dict 操作 ------------------


@register.filter
def dict_get(d, key):
    if d is None:
        return ""
    return d.get(key, "")


@register.filter
def get(dict_obj, key):
    return dict_obj.get(key)


@register.filter
def get_item(dictionary, key):
    return dictionary.get(key)


@register.filter
def get_item_nested(keyed_dict, key_pair):
    """支援用 (key1, key2) 查巢狀 dict，例如 all_notes|get_item_nested:(id, "favorite")"""
    if isinstance(key_pair, (list, tuple)) and len(key_pair) == 2:
        return keyed_dict.get(key_pair[0], {}).get(key_pair[1])
    return ""
