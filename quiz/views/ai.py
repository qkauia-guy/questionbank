import requests
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST, require_GET
from django.http import JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from ..models import Question
from django.contrib import messages
from urllib.parse import urlencode, urlparse, parse_qs
from django.contrib.auth.forms import UserCreationForm


# ✅ 封裝：發送 Prompt 給 Ollama 模型
def send_prompt_to_ollama(prompt, model="qwen2.5-coder:7b", timeout=300):
    try:
        response = requests.post(
            "http://localhost:11434/api/generate",
            json={"model": model, "prompt": prompt, "stream": False},
            timeout=timeout,
        )
        return response.json()
    except Exception as e:
        return {"response": f"⚠️ AI 請求錯誤：{e}"}


# ✅ AI 解釋主函式
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
        options = generate_options_text(question)

    prompt = f"""請使用繁體中文回答。
這是一題選擇題，請幫我解釋為什麼答案不是「{user_ans}」，而是「{correct_ans}」。
請特別根據「題目範圍」思考解釋。
科目範圍：「{category_text or '未提供'}」
題目內容如下：
{question_text}
選項如下：
{options}
""".strip()

    data = send_prompt_to_ollama(prompt, model=model_name)
    return f"� 本次回答由「{model_name}」模型生成：\n\n{data.get('response', '⚠️ AI 沒有回應。')}"


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
    if model:
        request.session["ollama_model"] = model
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
    model_name = request.session.get("ollama_model", "qwen2.5-coder:7b")

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

    data = send_prompt_to_ollama(prompt, model=model_name)
    reply = data.get("response", "⚠️ AI 沒有回應。")
    return render(request, "quiz/_followup_result.html", {"reply": reply})


# ✅ 產生格式化選項
def generate_options_text(question):
    options_text = ""
    for letter in "ABCDEFGH":
        choice = getattr(question, f"choice_{letter.lower()}", "").strip()
        if choice and choice.upper() != "X":
            options_text += f"{letter}. {choice}\n"
    return options_text
