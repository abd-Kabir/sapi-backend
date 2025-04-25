from django.db import models
from django.utils.translation import gettext_lazy as _

from apps.authentication.models import User
from apps.files.models import File
from config.models import BaseModel


class PostTypes(models.TextChoices):
    photo_video = 'photo_video', _('Фото/Видео')
    music = 'music', _('Музыка')
    file = 'file', _('Файл')
    questionnaire = 'questionnaire', _('Опросник')


class Post(BaseModel):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    post_type = models.CharField(max_length=20, choices=PostTypes.choices)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    files = models.ManyToManyField(File)

    class Meta:
        db_table = "post"


class QuestionnairePost(models.Model):
    text = models.TextField()
    allow_multiple_answers = models.BooleanField(default=False)
    post = models.OneToOneField(Post, on_delete=models.CASCADE, related_name='questionnaire_post')

    class Meta:
        db_table = 'post_questionnaire'


class AnswerOption(models.Model):
    text = models.CharField(max_length=255)
    is_correct = models.BooleanField(default=False)
    questionnaire_post = models.ForeignKey(QuestionnairePost, on_delete=models.CASCADE, related_name='answer_options')

    class Meta:
        db_table = 'answer_option'
