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
admin_creator_list_params = [
    openapi.Parameter(
        'search', openapi.IN_QUERY,
        description="Search value for username, temp_username, phone_number, or temp_phone_number",
        type=openapi.TYPE_STRING
    ),
    openapi.Parameter(
        'date_from', openapi.IN_QUERY,
        description="Filter users registered from this date (format: YYYY-MM-DD)",
        type=openapi.FORMAT_DATE
    ),
    openapi.Parameter(
        'date_to', openapi.IN_QUERY,
        description="Filter users registered up to this date (format: YYYY-MM-DD)",
        type=openapi.FORMAT_DATE
    ),
    openapi.Parameter(
        'category', openapi.IN_QUERY,
        description="Filter by Category ID",
        type=openapi.TYPE_INTEGER
    ),
    openapi.Parameter(
        'user_type', openapi.IN_QUERY,
        description="User type: 0 - User, 1 - Creator",
        type=openapi.TYPE_INTEGER,
        enum=[0, 1]
    ),
    openapi.Parameter(
        'status', openapi.IN_QUERY,
        description="User status: 0 - Inactive, 1 - Active, 2 - Blocked",
        type=openapi.TYPE_INTEGER,
        enum=[0, 1, 2]
    ),
    openapi.Parameter(
        'limit', openapi.IN_QUERY,
        description="Number of records per page",
        type=openapi.TYPE_INTEGER
    ),
    openapi.Parameter(
        'offset', openapi.IN_QUERY,
        description="The starting position of the records to retrieve",
        type=openapi.TYPE_INTEGER
    ),
]