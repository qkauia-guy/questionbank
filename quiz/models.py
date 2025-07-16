from django.db import models
from django.contrib.auth.models import User
from decimal import Decimal
from django.utils.timezone import localtime


class Question(models.Model):
    chapter = models.CharField(max_length=10)
    number = models.CharField(max_length=10)
    question_text = models.TextField()
    choice_a = models.TextField()
    choice_b = models.TextField()
    choice_c = models.TextField()
    choice_d = models.TextField()
    choice_e = models.TextField(default="`X`")
    choice_f = models.TextField(default="`X`")
    choice_g = models.TextField(default="`X`")
    choice_h = models.TextField(default="`X`")
    answer = models.CharField(max_length=20)  # 多個答案可用逗號分隔
    explanation = models.TextField(blank=True, default="")
    require_order = models.BooleanField(default=False)
    is_fill_in = models.BooleanField(default=False)
    fill_answer = models.CharField(max_length=30, blank=True, default="")
    category = models.CharField(max_length=50, default="DataBase")
    number_order = models.DecimalField(max_digits=10, decimal_places=0, default=0)
    image = models.ImageField(upload_to="question_images/", blank=True, null=True)

    def save(self, *args, **kwargs):
        try:
            parts = self.number.split("-")
            main = int(parts[0]) if len(parts) > 0 else 0
            sub = int(parts[1]) if len(parts) > 1 else 0
            sub_sub = int(parts[2]) if len(parts) > 2 else 0
            chapter_val = int(self.chapter)
            self.number_order = chapter_val * 10000 + main * 100 + sub_sub
        except ValueError:
            self.number_order = 0
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.chapter}-{self.number}"


class QuestionRecord(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    session_key = models.CharField(max_length=40, null=True, blank=True)
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    is_correct = models.BooleanField()
    answered_at = models.DateTimeField(auto_now_add=True)
    selected_answer = models.CharField(max_length=50, blank=True)
    used_time = models.IntegerField(default=0)
    ai_explanation = models.TextField(null=True, blank=True)
    fill_answer = models.CharField(max_length=100, blank=True, default="")
    source = models.CharField(
        max_length=20,
        choices=[("mock", "隨機測驗"), ("chapter", "章節練習")],
        default="mock",
    )

    exam_session = models.ForeignKey(
        "ExamSession",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="records",
    )

    def __str__(self):
        who = self.user.username if self.user else f"Session-{self.session_key}"
        return f"{who} - {self.question} - {'✔' if self.is_correct else '✘'}"


class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    ROLE_CHOICES = (
        ("admin", "管理員"),
        ("user", "一般使用者"),
    )
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default="user")

    def __str__(self):
        return f"{self.user.username} - {self.role}"


class ExamSession(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    session_key = models.CharField(max_length=40, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    category = models.CharField(max_length=100)
    finished_at = models.DateTimeField(null=True, blank=True)
    total_questions = models.IntegerField(default=20)
    score = models.FloatField(null=True, blank=True)  # 成績計算後填入
    is_submitted = models.BooleanField(default=False)
    current_index = models.IntegerField(default=0)

    questions = models.ManyToManyField(Question, related_name="exam_sessions")

    def __str__(self):
        who = self.user.username if self.user else f"Session-{self.session_key}"
        return f"{who} 的模擬考（{self.created_at.date()}）"

    @property
    def finished_at_local(self):
        return localtime(self.finished_at) if self.finished_at else None
