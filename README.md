# Quiz Question Bank

這是一個使用 Django 建立的線上題庫系統，支援選擇題、填空題、小畫家作答、章節分類與 AI 解釋功能。

## 主要功能

- 模擬測驗（章節與題號搜尋）
- 支援選擇題與填空題判斷
- 題號排序（格式如 1 - 2、10 - 1）
- 使用本地 Ollama AI 模型提供錯題說明
- 小畫家功能
- 錯題回饋與提示
- AI 模型：整合 qwen2.5-coder:3b 分析解釋錯誤原因

## � 資料模型

### Question (題目)

| 欄位名稱        | 資料型態                                | 說明                    |
| --------------- | --------------------------------------- | ----------------------- |
| `id`            | `AutoField`                             | 主鍵，自動生成          |
| `question_text` | `TextField`                             | 題目內容                |
| `answer`        | `CharField(max_length=10)`              | 正確答案（例如 AB）     |
| `chapter`       | `CharField(max_length=100)`             | 所屬章節                |
| `number`        | `CharField(max_length=20)`              | 題號（支援 1 - 1 格式） |
| `explanation`   | `TextField`                             | 答案說明                |
| `require_order` | `BooleanField`                          | 是否要求作答順序        |
| `is_fill_in`    | `BooleanField`                          | 是否為填空題            |
| `fill_answer`   | `CharField(max_length=100, blank=True)` | 填空正確答案            |

## 安裝與啟動方式

```bash
cd questionbank
git clone https://github.com/你的帳號/questionbank.git

python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt

python manage.py migrate
python manage.py runserver
```

## 測試

```bash
python manage.py test
```

## 動產生完整 requirements.txt

```bash
pip freeze > requirements.txt
```

## 匯出資料

可使用以下指令將資料導出：

```bash
python manage.py dumpdata quiz.Question --indent 2 > questions.json
python manage.py dumpdata quiz.Drawing --indent 2 > drawings.json
```

## 匯入資料

```bash
python manage.py loaddata questions.json
python manage.py loaddata drawings.json
```

# ⚠️ 注意事項：

因為 ExamSession 資料表已經存在，請在執行 migration 時使用：
`python manage.py migrate quiz --fake`
或是

- `python manage.py migrate quiz 0020 --fake`
- `python manage.py migrate quiz 0021 --fake`

作者：艸先生

- 資料庫題號自動更新
  `python manage.py update_number_order`

- 匯入資料
  `python manage.py shell < import_questions.py`
