from django.db.models import Q
from django_filters import rest_framework as filters

from apps.authentication.models import User


class AdminCreatorFilter(filters.FilterSet):
    search = filters.CharFilter(method='filter_search')
    date_from = filters.DateFilter(field_name='date_joined', lookup_expr='date__gte')
    date_to = filters.DateFilter(field_name='date_joined', lookup_expr='date__lte')
    category = filters.NumberFilter(field_name='category_id')
    user_type = filters.NumberFilter(method='filter_user_type')
    status = filters.NumberFilter(method='filter_status')

    class Meta:
        model = User
        fields = ['category_id']

    def filter_search(self, queryset, name, value):
        return queryset.filter(
            Q(username__icontains=value) |
            Q(temp_username__icontains=value) |
            Q(phone_number__icontains=value) |
            Q(temp_phone_number__icontains=value)
        )

    def filter_user_type(self, queryset, name, value):
        if value == 1:
            return queryset.filter(is_creator=True)
        elif value == 0:
            return queryset.filter(is_creator=False)
        return queryset

    def filter_status(self, queryset, name, value):
        if value == 0:
            return queryset.filter(is_creator=False)
        elif value == 1:
            return queryset.filter(is_creator=True, is_blocked_by__isnull=True)
        elif value == 2:
            return queryset.filter(is_blocked_by__isnull=False)
        return queryset
