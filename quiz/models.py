from django.db import models


class Question(models.Model):
    chapter = models.CharField(max_length=10)
    number = models.CharField(max_length=10)
    question_text = models.TextField()
    choice_a = models.TextField()
    choice_b = models.TextField()
    choice_c = models.TextField()
    choice_d = models.TextField()
    choice_e = models.TextField(default="X")
    choice_f = models.TextField(default="X")
    choice_g = models.TextField(default="X")
    choice_h = models.TextField(default="X")
    answer = models.CharField(max_length=20)  # 多個答案可用逗號分隔
    explanation = models.TextField(blank=True, default="")
    require_order = models.BooleanField(default=False)  # ✅ 是否順序正確
    is_fill_in = models.BooleanField(default=False)  # ✅ 是否為填空選擇題
    fill_answer = models.CharField(max_length=30, blank=True, default="")  # 填空題答案
    category = models.CharField(max_length=50, default="Python")  # 新增欄位：題庫分類

    def __str__(self):
        return f"{self.chapter}-{self.number}"
