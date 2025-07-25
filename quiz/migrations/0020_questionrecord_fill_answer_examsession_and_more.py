# Generated by Django 5.2.3 on 2025-07-15 14:14

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("quiz", "0019_question_image_alter_question_choice_e_and_more"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddField(
            model_name="questionrecord",
            name="fill_answer",
            field=models.CharField(blank=True, default="", max_length=100),
        ),
        # migrations.CreateModel(
        # name='ExamSession',
        # fields=[
        # ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
        # ('session_key', models.CharField(blank=True, max_length=40, null=True)),
        # ('created_at', models.DateTimeField(auto_now_add=True)),
        # ('category', models.CharField(max_length=100)),
        # ('finished_at', models.DateTimeField(blank=True, null=True)),
        # ('total_questions', models.IntegerField(default=20)),
        # ('score', models.FloatField(blank=True, null=True)),
        # ('is_submitted', models.BooleanField(default=False)),
        # ('current_index', models.IntegerField(default=0)),
        # ('questions', models.ManyToManyField(related_name='exam_sessions', to='quiz.question')),
        # ('user', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
        # ],
        # ),
        # migrations.AddField(
        # model_name='questionrecord',
        # name='exam_session',
        # field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='records', to='quiz.examsession'),
        # ),
    ]
