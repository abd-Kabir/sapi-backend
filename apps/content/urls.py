from django.urls import path
from rest_framework.routers import DefaultRouter

from apps.content.views import (PostCreateAPIView, CategoryModelViewSet, ChoiceTypeListAPIView,
                                PostAccessibilityAPIView, QuestionnairePostAnswerAPIView, PostByCategoryListAPIView,
                                PostToggleLikeAPIView, PostShowAPIView, PostShowCommentListAPIView,
                                PostShowRepliesListAPIView, PostLeaveCommentAPIView, CreateReportAPIView,
                                PostToggleSaveAPIView, PostByUserListAPIView, PostByFollowedListAPIView)

router = DefaultRouter()
router.register('category', CategoryModelViewSet, basename='category')

app_name = 'content'
urlpatterns = [
    path('choices/', ChoiceTypeListAPIView.as_view(), name='choices'),
    path('post/create/', PostCreateAPIView.as_view(), name='post_create'),
    path('post/<int:pk>/accessibility/', PostAccessibilityAPIView.as_view(), name='post_accessibility'),
    path('questionnaire-post/answer/', QuestionnairePostAnswerAPIView.as_view(), name='questionnaire_post_answer'),

    path('post/by-category/<int:category_id>/', PostByCategoryListAPIView.as_view(), name='post_by_category'),
    path('post/by-user/<int:user_id>/', PostByUserListAPIView.as_view(), name='post_by_user'),
    path('post/by-followed/', PostByFollowedListAPIView.as_view(), name='post_by_followed'),
    path('post/<int:pk>/show/', PostShowAPIView.as_view(), name='post_show'),
    path('post/<int:post_id>/show/comments/', PostShowCommentListAPIView.as_view(), name='post_show_comments'),
    path('post/show/comment/<int:comment_id>/replies/', PostShowRepliesListAPIView.as_view(),
         name='post_show_comment_replies'),
    path('post/toggle-like/', PostToggleLikeAPIView.as_view(), name='post_toggle_like'),
    path('post/leave-comment/', PostLeaveCommentAPIView.as_view(), name='post_leave_comment'),

    path('reports/create/', CreateReportAPIView.as_view(), name='create_report'),
    path('post/<int:post_id>/toggle-save/', PostToggleSaveAPIView.as_view(), name='post_toggle_save'),
]
urlpatterns += router.urls
