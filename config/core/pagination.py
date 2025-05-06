from math import ceil

from rest_framework import pagination
from rest_framework.response import Response


class APIPagination(pagination.PageNumberPagination):
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 500

    def get_paginated_response(self, data):
        return Response({
            'count': self.page.paginator.count,
            'total_pages': ceil(self.page.paginator.count / self.get_page_size(self.request)),
            'next': self.get_next_link(),
            'previous': self.get_previous_link(),
            'results': data
        })


class APILimitOffsetPagination(pagination.LimitOffsetPagination):
    default_limit = 10
    limit_query_param = 'limit'
    offset_query_param = 'offset'
    max_limit = 500

    def get_paginated_response(self, data):
        total_count = self.count
        limit = self.get_limit(self.request) or self.default_limit
        total_pages = ceil(total_count / limit) if limit else 0

        return Response({
            'count': total_count,
            'total_pages': total_pages,
            'next': self.get_next_link(),
            'previous': self.get_previous_link(),
            'results': data
        })
