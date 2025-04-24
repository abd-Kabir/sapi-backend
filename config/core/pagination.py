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
