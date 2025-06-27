from drf_yasg import openapi

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
status_swagger_param = openapi.Parameter(
    'status',
    openapi.IN_QUERY,
    description="Status code filter (integer)",
    type=openapi.TYPE_INTEGER
)