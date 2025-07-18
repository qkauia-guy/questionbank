import requests
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.http import JsonResponse
from django.shortcuts import render
from .base import convert_to_traditional
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_GET
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404
from ..models import Question
from django.contrib import messages
from django.shortcuts import redirect
from urllib.parse import urlencode, urlparse, parse_qs
from django.contrib.auth.forms import UserCreationForm


def get_ai_feedback_ollama(
    question_text,
    user_ans,
    correct_ans,
    question=None,
    category=None,
    options="",
    model_name="qwen2.5-coder:7b",
):
    user_ans = user_ans or "（未提供）"
    correct_ans = correct_ans or "（未提供）"
    category_text = category or (getattr(question, "category", "") or "").strip()

    if not options and question:
        for letter in "ABCDEFGH":
            choice_text = getattr(question, f"choice_{letter.lower()}", "").strip()
            if choice_text and choice_text.upper() != "X":
                options += f"{letter}. {choice_text}\n"

    prompt = f"""請使用繁體中文回答。
這是一題選擇題，請幫我解釋為什麼答案不是「{user_ans}」，而是「{correct_ans}」。
請特別根據「題目範圍」思考解釋。
科目範圍：「{category_text or '未提供'}」
題目內容如下：
{question_text}
選項如下：
{options}
""".strip()

    try:
        response = requests.post(
            "http://localhost:11434/api/generate",
            json={"model": model_name, "prompt": prompt, "stream": False},
            timeout=180,
        )
        data = response.json()
        return f"� 本次回答由「{model_name}」模型生成：\n\n{data.get('response', '⚠️ AI 沒有回應。')}"
    except Exception as e:
        return f"⚠️ AI 請求錯誤：{e}"


@require_GET
def toggle_ollama(request):
    enable = request.GET.get("enable") == "true"
    request.session["ollama_enabled"] = enable
    return JsonResponse({"status": "ok", "enabled": enable})


def clear_ollama_notice(request):
    request.session.pop("show_ollama_notice", None)
    return JsonResponse({"cleared": True})


def set_ollama_model(request):
    model = request.GET.get("model")
    print(f"🧪 後端收到模型設定：{model}")
    if model:
        request.session["ollama_model"] = model
        print("🧪 已寫入 session")
    return JsonResponse({"status": "ok", "model": model})


def register(request):
    if request.method == "POST":
        form = UserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect("login")
    else:
        form = UserCreationForm()

    return render(request, "registration/register.html", {"form": form})


def is_ollama_running():
    try:
        response = requests.get("http://localhost:11434")
        return response.status_code == 200
    except:
        return False


# def is_ollama_running():
#     try:
#         response = requests.get("http://192.168.0.101:11434/api/tags", timeout=3)
#         return response.status_code == 200
#     except Exception:
#         return False


@login_required
@require_POST
def save_ai_explanation(request, pk):
    question = get_object_or_404(Question, pk=pk)
    new_explanation = request.POST.get("explanation")

    if new_explanation:
        question.explanation = new_explanation
        question.save()
        messages.success(request, "✅ 解釋已成功寫入")
    else:
        messages.warning(request, "⚠️ 沒有收到解釋內容")

    # ⏩ 回到來源頁面並觸發下一題
    referer = request.META.get("HTTP_REFERER", "/")
    parsed = urlparse(referer)
    base_url = parsed.path
    query = parse_qs(parsed.query)
    query["next"] = ["1"]

    return redirect(f"{base_url}?{urlencode(query, doseq=True)}")


@csrf_exempt
@login_required
@require_POST
def ask_ai_followup(request):
    question_text = request.POST.get("question_text", "")
    category = request.POST.get("category", "")
    options = request.POST.get("options", "")
    followup = request.POST.get("followup", "")
    chat_history = request.POST.get("chat_history", "")

    prompt = f"""以下是使用者與 AI 的過往對話：

{chat_history.strip()}

---

原始題目：
{question_text}

範圍：「{category}」
選項：
{options}

使用者的新問題：
{followup}

請用繁體中文回答。
"""

    response = requests.post(
        "http://localhost:11434/api/generate",
        json={"model": "qwen2.5-coder:7b", "prompt": prompt, "stream": False},
        timeout=90,
    )
    data = response.json()
    reply = data.get("response", "⚠️ AI 沒有回應。")

    return render(request, "quiz/_followup_result.html", {"reply": reply})


def generate_options_text(question):
    """
    根據題目自動產生選項文字（不含 "X" 的選項），給 AI 用的提示格式。
    """
    options_text = ""
    for letter in "ABCDEFGH":
        choice = getattr(question, f"choice_{letter.lower()}", "").strip()
        if choice and choice.upper() != "X":
            options_text += f"{letter}. {choice}\n"
    return options_text
