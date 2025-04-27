from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from rest_framework.exceptions import ValidationError

from apps.authentication.models import User
from apps.files.models import File
from config.models import BaseModel


class PostTypes(models.TextChoices):
    photo_video = 'photo_video', _('Фото/Видео')
    music = 'music', _('Музыка')
    file = 'file', _('Файл')
    questionnaire = 'questionnaire', _('Опросник')


class ReportTypes(models.TextChoices):
    COPYRIGHT = 'copyright', _('Контент, нарушающий авторские права третьих лиц')
    EXTREMISM = 'extremism', _('Материалы экстремистского, террористического характера')
    DISCRIMINATION = 'discrimination', _('Дискриминация по расовому, половому, религиозному и другим признакам')
    PORNOGRAPHY = 'pornography', _('Порнографические материалы и контент для взрослых')
    VIOLENCE = 'violence', _('Агрессивный, жестокий или призывающий к насилию контент')
    DRUGS_ALCOHOL = 'drugs_alcohol', _('Призывы к употреблению наркотических веществ и алкоголя')
    MISLEADING = 'misleading', _('Введение пользователей в заблуждение (мошенничество, спам, фейковые сборы средств)')
    PERSONAL_DATA = 'personal_data', _('Контент, содержащий личные данные третьих лиц без их согласия')
    OTHER = 'other', _('Другое')


class Category(BaseModel):
    name = models.CharField(max_length=155)

    class Meta:
        db_table = 'category'


# TODO: signals for updating likes, comments count
# @receiver([post_save, post_delete], sender=Like)
# def update_like_count(sender, instance, **kwargs):
#     instance.post.update_counts()
#
# @receiver([post_save, post_delete], sender=Comment)
# def update_comment_count(sender, instance, **kwargs):
#     instance.post.update_counts()
# @receiver([post_save, post_delete], sender=Like)
# def update_like_counts(sender, instance, **kwargs):
#     if instance.post:
#         instance.post.update_counts()
#     if instance.comment:
#         instance.comment.update_like_count()


class Post(BaseModel):
    is_deleted = models.BooleanField(default=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    title = models.CharField(max_length=255, blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    post_type = models.CharField(max_length=20, choices=PostTypes.choices)

    like_count = models.PositiveIntegerField(default=0)
    comment_count = models.PositiveIntegerField(default=0)

    files = models.ManyToManyField(File)
    allow_multiple_answers = models.BooleanField(default=False)  # only for questionnaire
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, related_name='posts')

    def has_liked(self, user):
        return self.likes.filter(user=user).exists()

    def is_reported_by(self, user):
        return self.reports.filter(user=user).exists()

    def update_counts(self):
        self.like_count = self.likes.count()
        self.comment_count = self.comments.count()
        self.save()
        # Update all comment's like counts
        for comment in self.comments.all():
            comment.update_like_count()

    class Meta:
        db_table = "post"


# class QuestionnairePost(models.Model):
#     text = models.TextField()
#     allow_multiple_answers = models.BooleanField(default=False)
#     post = models.OneToOneField(Post, on_delete=models.CASCADE, related_name='questionnaire_post')
#
#     class Meta:
#         db_table = 'post_questionnaire'


class AnswerOption(models.Model):
    text = models.CharField(max_length=155)
    is_correct = models.BooleanField(default=False)
    questionnaire_post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='answers')

    class Meta:
        db_table = 'post_questionnaire_answer'


class Comment(BaseModel):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='comments')
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='comments')
    text = models.TextField()
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='replies')

    like_count = models.PositiveIntegerField(default=0)

    def has_liked(self, user):
        return self.likes.filter(user=user).exists()

    def update_like_count(self):
        self.like_count = self.likes.count()
        self.save()

    class Meta:
        db_table = 'comment'
        ordering = ['-created_at']


class Like(BaseModel):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='likes')
    post = models.ForeignKey(Post, on_delete=models.SET_NULL, related_name='likes', null=True, blank=True)
    comment = models.ForeignKey(Comment, on_delete=models.SET_NULL, related_name='likes', null=True, blank=True)

    def clean(self):
        if not self.post and not self.comment:
            raise ValidationError("Like must be associated with either a post or comment")
        if self.post and self.comment:
            raise ValidationError("Like can only be associated with either a post or comment, not both")
        super().clean()

    class Meta:
        db_table = 'like'
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'post'],
                name='unique_user_post_like',
                condition=models.Q(comment__isnull=True)
            ),
            models.UniqueConstraint(
                fields=['user', 'comment'],
                name='unique_user_comment_like',
                condition=models.Q(post__isnull=True)
            ),
            models.CheckConstraint(
                check=models.Q(post__isnull=False) | models.Q(comment__isnull=False),
                name='like_must_have_post_or_comment'
            )
        ]


class Report(BaseModel):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reports')
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='reports')
    report_type = models.CharField(max_length=20, choices=ReportTypes.choices)
    description = models.TextField(blank=True, null=True)
    is_resolved = models.BooleanField(default=False)
    resolved_at = models.DateTimeField(null=True, blank=True)
    resolved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True,
                                    related_name='resolved_reports')

    def resolve(self, resolved_by_user):
        self.is_resolved = True
        self.resolved_at = timezone.now()
        self.resolved_by = resolved_by_user
        self.save()

    class Meta:
        db_table = 'report'
        unique_together = ('user', 'post')
