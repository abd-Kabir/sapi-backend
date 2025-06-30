import django_filters

from apps.authentication.models import NotificationDistribution
from apps.content.models import Report


class ReportFilter(django_filters.FilterSet):
    report_type = django_filters.CharFilter(field_name='report_type', lookup_expr='iexact')

    date_from = django_filters.DateFilter(field_name='created_at', lookup_expr='gte')
    date_to = django_filters.DateFilter(field_name='created_at', lookup_expr='lte')

    status = django_filters.NumberFilter(field_name='status')

    class Meta:
        model = Report
        fields = ['report_type', 'date_from', 'date_to', 'status']


class NotifDisFilter(django_filters.FilterSet):
    user_type = django_filters.CharFilter(field_name='user_type')
    # types = django_filters.CharFilter(method='filter_types')
    types = django_filters.BaseInFilter(field_name='types', lookup_expr='overlap')

    date_from = django_filters.DateFilter(field_name='created_at', lookup_expr='gte')
    date_to = django_filters.DateFilter(field_name='created_at', lookup_expr='lte')

    status = django_filters.CharFilter(field_name='status')

    # def filter_types(self, queryset, name, value):
    #     filter_value = value.split(',')
    #     return queryset.filter(types__overlap=filter_value)

    class Meta:
        model = NotificationDistribution
        fields = ['date_from', 'date_to', 'status', 'types', 'user_type']
