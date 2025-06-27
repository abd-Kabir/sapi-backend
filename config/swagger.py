from drf_yasg import openapi

from apps.content.models import ReportStatusTypes, PostTypes

query_choice_swagger_param = openapi.Parameter(
    'type',
    openapi.IN_QUERY,
    description='Choice Type Filter',
    type=openapi.TYPE_STRING,
    required=False,
    enum=['post', 'report']
)
query_search_swagger_param = openapi.Parameter(
    'search',
    openapi.IN_QUERY,
    description='Search filter',
    type=openapi.TYPE_STRING,
    required=False,
)
report_type_swagger_param = openapi.Parameter(
    'report_type',
    openapi.IN_QUERY,
    description='Filter by report type (case-insensitive)',
    type=openapi.TYPE_STRING
)
date_from_swagger_param = openapi.Parameter(
    'date_from',
    openapi.IN_QUERY,
    description='Start date (YYYY-MM-DD) to filter reports',
    type=openapi.TYPE_STRING,
    format=openapi.FORMAT_DATE
)
date_to_swagger_param = openapi.Parameter(
    'date_to',
    openapi.IN_QUERY,
    description='End date (YYYY-MM-DD) to filter reports',
    type=openapi.TYPE_STRING,
    format=openapi.FORMAT_DATE
)

status_choices_description = '\n'.join([
    f'{value} - {label}'
    for value, label in ReportStatusTypes.choices
])
report_status_swagger_param = openapi.Parameter(
    'status',
    openapi.IN_QUERY,
    description=f'Status code filter (integer):\n{status_choices_description}',
    type=openapi.TYPE_INTEGER,
    enum=[i for i, j in ReportStatusTypes.choices]
)

status_choices_description = '\n'.join([
    f'{value} - {label}'
    for value, label in PostTypes.choices
])
post_type_swagger_param = openapi.Parameter(
    'post_type',
    openapi.IN_QUERY,
    description=f'Post type code filter, choices: \n{status_choices_description}',
    type=openapi.TYPE_STRING,
    enum=[i for i, j in PostTypes.choices]
)
admin_creator_list_params = [
    query_search_swagger_param,
    openapi.Parameter(
        'date_from', openapi.IN_QUERY,
        description='Filter users registered from this date (format: YYYY-MM-DD)',
        type=openapi.FORMAT_DATE
    ),
    openapi.Parameter(
        'date_to', openapi.IN_QUERY,
        description='Filter users registered up to this date (format: YYYY-MM-DD)',
        type=openapi.FORMAT_DATE
    ),
    openapi.Parameter(
        'category', openapi.IN_QUERY,
        description='Filter by Category ID',
        type=openapi.TYPE_INTEGER
    ),
    openapi.Parameter(
        'user_type', openapi.IN_QUERY,
        description='User type: 0 - User, 1 - Creator',
        type=openapi.TYPE_INTEGER,
        enum=[0, 1]
    ),
    openapi.Parameter(
        'status', openapi.IN_QUERY,
        description='User status: 0 - Inactive, 1 - Active, 2 - Blocked',
        type=openapi.TYPE_INTEGER,
        enum=[0, 1, 2]
    ),
    openapi.Parameter(
        'limit', openapi.IN_QUERY,
        description='Number of records per page',
        type=openapi.TYPE_INTEGER
    ),
    openapi.Parameter(
        'offset', openapi.IN_QUERY,
        description='The starting position of the records to retrieve',
        type=openapi.TYPE_INTEGER
    ),
]

period_swagger_param = openapi.Parameter(
    'period',
    openapi.IN_QUERY,
    description='Time period for grouping data points',
    type=openapi.TYPE_STRING,
    enum=['day', 'week', 'month'],
    default='day'
)
start_date_swagger_param = openapi.Parameter(
    'start_date',
    openapi.IN_QUERY,
    description='Start date for analytics (YYYY-MM-DD).',
    type=openapi.TYPE_STRING,
    format=openapi.FORMAT_DATE,
    example='2025-06-01'
)
end_date_swagger_param = openapi.Parameter(
    'end_date',
    openapi.IN_QUERY,
    description='End date for analytics (YYYY-MM-DD).',
    type=openapi.TYPE_STRING,
    format=openapi.FORMAT_DATE,
    example='2025-06-25'
)
dashboard_user_type_swagger_param = openapi.Parameter(
    'user_type',
    openapi.IN_QUERY,
    description="Filter analytics by user type",
    type=openapi.TYPE_STRING,
    enum=['all', 'creators', 'users'],
    default='all'
)
