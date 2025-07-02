from django.db import models
from django.contrib.auth.models import User


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
    require_order = models.BooleanField(default=False)
    is_fill_in = models.BooleanField(default=False)
    fill_answer = models.CharField(max_length=30, blank=True, default="")
    category = models.CharField(max_length=50, default="Python")

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

    def __str__(self):
        who = self.user.username if self.user else f"Session-{self.session_key}"
        return f"{who} - {self.question} - {'✔' if self.is_correct else '✘'}"
