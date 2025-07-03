# 匯入必要的模組
import random  # 用於隨機選擇題目
import requests  # 用於發送 HTTP 請求 (呼叫 AI 模型)
import json  # 用於處理 JSON 數據 (雖然在此程式碼中未直接使用，但 requests 內部會用到)
from django.shortcuts import render, redirect  # Django 的捷徑功能，用於渲染模板和重定向
from .models import Question, QuestionRecord  # 從本地 models.py 匯入資料庫模型
from django.http import JsonResponse  # 用於回傳 JSON 格式的 HTTP 回應
from django.contrib.auth.decorators import (
    login_required,
)  # 用於限制視圖只能被登入的使用者訪問


@login_required
def exam_history(request):
    records = (
        QuestionRecord.objects.filter(user=request.user)
        .select_related("question")
        .order_by("-answered_at")
    )
    return render(request, "quiz/exam_history.html", {"records": records})


@login_required
def review_wrong_questions(request):
    wrong_records = (
        QuestionRecord.objects.filter(user=request.user, is_correct=False)
        .select_related("question")
        .order_by("-answered_at")  # ✅ 修正這一行
    )

    questions = [record.question for record in wrong_records]

    return render(
        request,
        "quiz/review_wrong_questions.html",
        {
            "questions": questions,
            "records": wrong_records,
        },
    )


def get_next_question(exclude_id=None):
    questions = Question.objects.all().order_by("chapter", "number")
    if exclude_id:
        questions = questions.exclude(id=exclude_id)
    return questions.first() if questions.exists() else None


def check_answer(question, selected_answer, fill_input):
    correct_answer = question.answer.upper()
    if question.is_fill_in:
        return fill_input.strip() == question.fill_answer.strip()
    else:
        user_ans = "".join(selected_answer).strip().upper()
        if question.require_order:
            return user_ans == correct_answer
        else:
            return sorted(user_ans) == sorted(correct_answer)


def reset_chapter_practice(request):
    if "question_ids" in request.session:
        del request.session["question_ids"]
    if "current_index" in request.session:
        del request.session["current_index"]
    return redirect("chapter_practice")


@login_required
def chapter_practice(request):
    chapter = request.GET.get("chapter")
    number = request.GET.get("number")

    # 篩選題目
    questions = Question.objects.order_by("chapter", "number")
    if chapter:
        questions = questions.filter(chapter=chapter)
    if number:
        questions = questions.filter(number=number)

    total_question_count = Question.objects.count()

    if total_question_count == 0:
        return render(request, "quiz/chapter_practice.html", {"no_question": True})

    # 初始化 index
    if "current_index" not in request.session:
        request.session["current_index"] = 0

    # 按下重新開始
    if "restart" in request.POST:
        request.session["current_index"] = 0
        return redirect("chapter_practice")

    # 上一題
    if "prev" in request.POST:
        request.session["current_index"] = max(request.session["current_index"] - 1, 0)
        return redirect("chapter_practice")

    # 跳過
    if "skip" in request.POST:
        if request.session["current_index"] < total_question_count - 1:
            request.session["current_index"] += 1
        return redirect("chapter_practice")

    # ✅ 安全地取得 current_index 並防止越界
    current_index = request.session.get("current_index", 0)
    if current_index >= total_question_count:
        current_index = max(total_question_count - 1, 0)
        request.session["current_index"] = current_index

    # 取得目前題目
    question = questions[current_index]

    selected_answer = [a.upper() for a in request.POST.getlist("selected_answer")]
    fill_input = request.POST.get("fill_answer", "").strip()
    result = None
    correct_answer = None
    ai_explanation = None

    # 送出答案後批改
    if request.method == "POST" and "next" not in request.POST:
        result = check_answer(question, selected_answer, fill_input)
        correct_answer = question.answer
        used_time = request.POST.get("used_time", 0)

        # 儲存作答記錄
        QuestionRecord.objects.create(
            user=request.user,
            question=question,
            is_correct=result,
            selected_answer=(
                "".join(selected_answer) if not question.is_fill_in else fill_input
            ),
            used_time=used_time,
        )

        # 若答錯，呼叫 AI 解釋
        if not result:
            ai_explanation = get_ai_feedback_ollama(
                question.question_text,
                fill_input if question.is_fill_in else "".join(selected_answer),
                correct_answer,
            )

    # 下一題
    if "next" in request.POST:
        if request.session["current_index"] < total_question_count - 1:
            request.session["current_index"] += 1
        return redirect("chapter_practice")

    # 下拉選單資料
    chapter_list = Question.objects.values_list("chapter", flat=True).distinct()
    number_list = (
        Question.objects.filter(chapter=chapter)
        .values_list("number", flat=True)
        .distinct()
        if chapter
        else []
    )

    return render(
        request,
        "quiz/chapter_practice.html",
        {
            "question": question,
            "selected_answer": selected_answer,
            "fill_input": fill_input,
            "result": result,
            "correct_answer": correct_answer,
            "ai_explanation": ai_explanation,
            "total_question_count": total_question_count,
            "current_index": current_index + 1,  # 顯示用（第幾題）
            "chapter_list": chapter_list,
            "number_list": number_list,
            "category": chapter,
            "number": number,
        },
    )


# 根據章節取得題號列表的 API視圖
def get_numbers_by_chapter(request):
    """
    這是一個非同步請求的處理函式 (API Endpoint)。
    當使用者在前端選擇一個章節時，前端會發送一個 GET 請求到此視圖，
    以取得該章節下所有的題號列表。
    """
    # 從 GET 請求中獲取 'chapter' 參數
    chapter = request.GET.get("chapter")
    # 從資料庫中篩選出指定章節的所有問題，並取得不重複的題號 ('number') 列表
    numbers = list(
        Question.objects.filter(chapter=chapter)
        .values_list("number", flat=True)
        .distinct()
    )

    # 定義一個排序鍵函式，用於處理 "主-子" 格式的題號 (例如 "3-1")
    def sort_key(val):
        try:
            # 去除字串中的空白
            cleaned = val.replace(" ", "")
            # 如果題號包含 '-'，則將其分割為主、子部分，並轉換為整數元組以便排序
            if "-" in cleaned:
                parts = cleaned.split("-")
                return (int(parts[0]), int(parts[1]))
            # 如果不包含 '-'，則視為只有主部分，子部分設為 0
            else:
                return (int(cleaned), 0)
        except Exception:
            # 如果轉換失敗 (例如題號格式不符預期)，則將其排在最後
            return (float("inf"), float("inf"))

    # 使用自訂的排序鍵對題號列表進行排序
    sorted_numbers = sorted(numbers, key=sort_key)
    # 以 JSON 格式回傳排序後的題號列表
    return JsonResponse({"numbers": sorted_numbers})


# 顯示全部題目列表的視圖
def question_list(request):
    """
    這個視圖會從資料庫中取得所有的問題，
    並將它們渲染到 question_list.html 模板上。
    """
    # 查詢 Question 模型中的所有物件
    questions = Question.objects.all()
    # 渲染模板，並將查詢到的 questions 物件傳遞給模板
    return render(request, "quiz/question_list.html", {"questions": questions})


# 題庫分類選擇頁面的視圖
def select_category(request):
    """
    這個視圖會取得所有不重複的「分類」(category)，
    讓使用者可以在一個頁面上選擇要測驗的分類。
    """
    # 從 Question 模型中取得所有不重複的 'category' 值
    categories = Question.objects.values_list("category", flat=True).distinct()
    # 渲染選擇分類的模板，並傳遞分類列表
    return render(request, "quiz/select_category.html", {"categories": categories})


# 呼叫本地 Ollama 模型獲得補充說明的函式
def get_ai_feedback_ollama(question_text, user_ans, correct_ans):
    """
    這個函式負責與本地運行的 Ollama AI 模型進行通訊。
    它會傳送題目、使用者答案和正確答案給 AI，並請求 AI 生成解釋。
    """
    # 建立提示 (Prompt)，引導 AI 解釋為什麼使用者的答案是錯的，而正確答案是對的
    prompt = f"""
這是一題選擇題，請幫我解釋這題的答案為什麼不是「{user_ans}」，而是「{correct_ans}」，內容如下：

{question_text}
"""
    try:
        # 使用 requests.post 向本地 Ollama 服務的 API 端點發送請求
        response = requests.post(
            "http://localhost:11434/api/generate",  # Ollama 的 API URL
            json={
                "model": "qwen2.5-coder:3b",
                "prompt": prompt,
                "stream": False,
            },  # 請求的內容，包含模型名稱、提示和設定
            timeout=90,  # 設定請求超時時間為 90 秒
        )
        # 解析回傳的 JSON 數據
        data = response.json()
        # 回傳 AI 生成的回應，如果沒有回應則回傳一條警告訊息
        return data.get("response", "⚠️ AI 沒有回應。")
    except Exception as e:
        # 如果請求過程中發生任何錯誤 (例如連線失敗、超時)，則回傳錯誤訊息
        return f"⚠️ AI 請求錯誤：{e}"


# 模擬測驗主邏輯的視圖
def mock_exam(request):
    """
    這是測驗功能的核心視圖。它處理以下幾件事：
    1. 根據使用者選擇的章節和題號篩選題目。
    2. 如果是 GET 請求，隨機顯示一題。
    3. 如果是 POST 請求，則代表使用者提交了答案，此視圖會進行批改。
    4. 批改後，顯示結果、正確答案和解釋。
    5. 如果答錯，會呼叫 AI 產生額外的補充說明。
    6. 記錄使用者的作答歷史。
    """
    # 從 GET 請求中獲取章節和題號參數
    category = request.GET.get("chapter")
    number = request.GET.get("number")

    # 初始化一些變數，用於儲存作答結果和相關資訊
    result = None
    correct_answer = None
    explanation = None
    selected_answer = []
    ai_explanation = None
    fill_input = ""

    # 根據提供的章節和題號參數篩選問題
    questions = Question.objects.all()
    if category:
        questions = questions.filter(chapter=category)
    if number:
        questions = questions.filter(number=number)

    # 如果根據篩選條件找不到任何問題
    if not questions.exists():
        # 準備章節和題號列表，供模板中的下拉選單使用
        chapter_list = Question.objects.values_list("chapter", flat=True).distinct()
        number_list = (
            Question.objects.filter(chapter=category)
            .values_list("number", flat=True)
            .distinct()
            if category
            else []
        )
        # 渲染測驗頁面，並傳遞一個標記表示沒有找到題目
        return render(
            request,
            "quiz/mock_exam.html",
            {
                "no_question": True,
                "chapter_list": chapter_list,
                "number_list": number_list,
                "category": category,
                "number": number,
            },
        )

    # 如果使用者點擊 "下一題" 或 "跳過"，直接重新導向到測驗頁面以載入新題目
    if request.method == "POST" and ("next" in request.POST or "skip" in request.POST):
        return redirect("mock_exam")

    # 如果請求方法是 POST (代表使用者提交答案)
    if request.method == "POST":
        # 從 POST 請求中獲取問題 ID
        question_id = request.POST.get("question_id")
        try:
            # 根據 ID 從資料庫中找到對應的問題物件
            question = Question.objects.get(id=question_id)
        except Question.DoesNotExist:
            # 如果找不到問題，顯示錯誤頁面
            return render(request, "quiz/mock_exam.html", {"no_question": True})

        # 獲取使用者選擇的答案 (適用於多選題) 和填空的答案
        selected_answer = request.POST.getlist("selected_answer")
        fill_input = request.POST.get("fill_answer", "").strip()

        # 獲取使用者作答花費的時間
        try:
            used_time = int(request.POST.get("used_time", 0))
        except (ValueError, TypeError):
            used_time = 0

        # 從問題物件中獲取正確答案、解釋和是否需要順序
        correct_answer = question.answer.upper()
        explanation = question.explanation
        require_order = question.require_order

        # 根據題目類型（填充或選擇）來判斷答案是否正確
        if question.is_fill_in:
            # 如果是填充題，直接比對使用者輸入和正確答案
            result = fill_input == question.fill_answer.strip()
        else:
            # 如果是選擇題，將使用者選擇的選項組合成字串
            user_ans = "".join(selected_answer).strip().upper()
            if require_order:
                # 如果需要考慮順序，直接比對字串
                result = user_ans == correct_answer
            else:
                # 如果不需要考慮順序，將兩個字串排序後再比對
                result = sorted(user_ans) == sorted(correct_answer)

        # 如果使用者回答錯誤
        if not result:
            try:
                # 呼叫 Ollama AI 獲取補充解釋
                ai_explanation = get_ai_feedback_ollama(
                    question.question_text, "".join(selected_answer), correct_answer
                )
            except Exception as e:
                ai_explanation = f"⚠️ AI 補充失敗：{e}"

        # 如果使用者已登入，則記錄這次作答
        if request.user.is_authenticated:
            QuestionRecord.objects.create(
                user=request.user,
                question=question,
                is_correct=result,
                selected_answer=(
                    ",".join(selected_answer) if not question.is_fill_in else fill_input
                ),
                # 記錄使用者花費的時間
                used_time=used_time,
            )
    else:
        # 如果請求方法是 GET (初次載入頁面或重新整理)
        # 從已篩選的問題中隨機選擇一題
        question = random.choice(questions)

    # 準備模板需要的所有章節列表
    chapter_list = Question.objects.values_list("chapter", flat=True).distinct()
    # 獲取當前問題所在的章節
    current_chapter = category or getattr(question, "chapter", None)

    # 如果有當前章節，則獲取該章節下的所有題號列表並排序
    if current_chapter:
        raw_numbers = (
            Question.objects.filter(chapter=current_chapter)
            .values_list("number", flat=True)
            .distinct()
        )

        # (此處的排序邏輯與 get_numbers_by_chapter 函式中的相同)
        def sort_key(val):
            try:
                cleaned = val.replace(" ", "")
                if "-" in cleaned:
                    parts = cleaned.split("-")
                    return (int(parts[0]), int(parts[1]))
                else:
                    return (int(cleaned), 0)
            except Exception:
                return (float("inf"), float("inf"))

        number_list = sorted(raw_numbers, key=sort_key)
    else:
        number_list = []

    # 渲染最終的測驗頁面，並傳入所有需要的變數
    return render(
        request,
        "quiz/mock_exam.html",
        {
            "question": question,  # 當前題目物件
            "selected_answer": selected_answer,  # 使用者選擇的答案
            "result": result,  # 批改結果 (True/False)
            "correct_answer": correct_answer,  # 正確答案
            "explanation": explanation,  # 官方解釋
            "category": category,  # 當前選擇的章節
            "number": number,  # 當前選擇的題號
            "ai_explanation": ai_explanation,  # AI 的補充說明
            "chapter_list": chapter_list,  # 所有章節的列表
            "number_list": number_list,  # 當前章節的題號列表
            "fill_input": fill_input,  # 使用者填空的輸入
        },
    )
