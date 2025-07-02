import sqlite3
import os
from django.core.management.base import BaseCommand
from quiz.models import Question


class Command(BaseCommand):
    help = "一次匯入所有 SQLite 題庫檔案中的題目"

    def handle(self, *args, **kwargs):
        db_files = [f for f in os.listdir() if f.endswith(".db")]
        total = 0

        for db_file in db_files:
            if not os.path.exists(db_file):
                self.stderr.write(self.style.WARNING(f"⚠️ 找不到 {db_file}，略過"))
                continue

            if "mysql" in db_file.lower():
                category = "MySQL"
            elif "html" in db_file.lower():
                category = "HTML"
            else:
                category = "Python"

            self.stdout.write(
                self.style.NOTICE(f"� 匯入中：{db_file} (分類：{category})")
            )

            try:
                conn = sqlite3.connect(db_file)
                cursor = conn.cursor()
                cursor.execute(
                    """
                    SELECT chapter, number, question_text,
                           choice_a, choice_b, choice_c, choice_d,
                           answer, explanation, require_order, is_fill_in
                    FROM question
                    """
                )
                rows = cursor.fetchall()
            except Exception as e:
                self.stderr.write(self.style.ERROR(f"❌ 匯入失敗：{e}"))
                continue

            for row in rows:
                Question.objects.create(
                    chapter=row[0],
                    number=row[1],
                    question_text=row[2],
                    choice_a=row[3],
                    choice_b=row[4],
                    choice_c=row[5],
                    choice_d=row[6],
                    answer=row[7],
                    explanation=row[8],
                    require_order=bool(row[9]),
                    is_fill_in=bool(row[10]),
                    category=category,
                )
            conn.close()
            self.stdout.write(self.style.SUCCESS(f"✅ {db_file} 匯入 {len(rows)} 筆"))
            total += len(rows)

        self.stdout.write(self.style.SUCCESS(f"� 匯入完成，共匯入 {total} 筆題目"))
