import django_filters

from apps.content.models import Post, PostTypes


class PostByUserFilter(django_filters.FilterSet):
    post_type = django_filters.ChoiceFilter(
        choices=PostTypes.choices, label='Тип поста', lookup_expr='exact'
    )

    class Meta:
        model = Post
        fields = ['post_type', ]
