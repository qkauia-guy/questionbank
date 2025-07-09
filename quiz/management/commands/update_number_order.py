from django.core.management.base import BaseCommand
from quiz.models import Question


class Command(BaseCommand):
    help = "重新計算所有題目的 number_order"

    def handle(self, *args, **kwargs):
        count = 0
        for q in Question.objects.all():
            q.save()
            count += 1
        self.stdout.write(self.style.SUCCESS(f"{count} 題已更新 number_order"))
