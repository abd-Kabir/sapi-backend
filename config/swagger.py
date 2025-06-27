from drf_yasg import openapi

from apps.content.models import ReportStatusTypes

report_type_swagger_param = openapi.Parameter(
    'report_type',
    openapi.IN_QUERY,
    description="Filter by report type (case-insensitive)",
    type=openapi.TYPE_STRING
)
date_from_swagger_param = openapi.Parameter(
    'date_from',
    openapi.IN_QUERY,
    description="Start date (YYYY-MM-DD) to filter reports",
    type=openapi.TYPE_STRING,
    format=openapi.FORMAT_DATE
)
date_to_swagger_param = openapi.Parameter(
    'date_to',
    openapi.IN_QUERY,
    description="End date (YYYY-MM-DD) to filter reports",
    type=openapi.TYPE_STRING,
    format=openapi.FORMAT_DATE
)

status_choices_description = "\n".join([
    f"{value} - {label}"
    for value, label in ReportStatusTypes.choices
])
report_status_swagger_param = openapi.Parameter(
    'status',
    openapi.IN_QUERY,
    description=f"Status code filter (integer):\n{status_choices_description}",
    type=openapi.TYPE_INTEGER,
    enum=[i for i, j in ReportStatusTypes.choices]
)