import django_filters
from django.db.models import Q

from apps.authentication.models import NotificationDistribution, User
from apps.content.models import Report


class AdminCreatorFilter(django_filters.FilterSet):
    search = django_filters.CharFilter(method='filter_search')
    date = django_filters.DateFilter(field_name='date_joined', lookup_expr='date')
    category = django_filters.NumberFilter(field_name='category_id')
    user_type = django_filters.NumberFilter(method='filter_user_type')
    status = django_filters.NumberFilter(method='filter_status')

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


class ReportFilter(django_filters.FilterSet):
    report_type = django_filters.CharFilter(field_name='report_type', lookup_expr='iexact')

    date = django_filters.DateFilter(field_name='created_at', lookup_expr='date')

    status = django_filters.NumberFilter(field_name='status')

    category_id = django_filters.NumberFilter(field_name='post__category__id')

    class Meta:
        model = Report
        fields = ['report_type', 'date', 'status', 'category_id']


class NotifDisFilter(django_filters.FilterSet):
    user_type = django_filters.CharFilter(field_name='user_type')
    # types = django_filters.CharFilter(method='filter_types')
    types = django_filters.BaseInFilter(field_name='types', lookup_expr='overlap')

    date = django_filters.DateFilter(field_name='created_at', lookup_expr='date')

    status = django_filters.CharFilter(field_name='status')

    # def filter_types(self, queryset, name, value):
    #     filter_value = value.split(',')
    #     return queryset.filter(types__overlap=filter_value)

    class Meta:
        model = NotificationDistribution
        fields = ['date', 'status', 'types', 'user_type']
