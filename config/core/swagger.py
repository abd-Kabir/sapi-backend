from drf_yasg import openapi

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
    description='Search, Creators',
    type=openapi.TYPE_STRING,
    required=False,
)
