import django_filters

from apps.content.models import Report


class ReportFilter(django_filters.FilterSet):
    report_type = django_filters.CharFilter(field_name='report_type', lookup_expr='iexact')

    date_from = django_filters.DateFilter(field_name='created_at', lookup_expr='gte')
    date_to = django_filters.DateFilter(field_name='created_at', lookup_expr='lte')

    status = django_filters.NumberFilter(field_name='status')

    class Meta:
        model = Report
        fields = ['report_type', 'date_from', 'date_to', 'status']