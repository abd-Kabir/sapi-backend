from rest_framework import status
from rest_framework.exceptions import APIException
from rest_framework.views import exception_handler

import logging

logger = logging.getLogger()


class APIValidation(APIException):
    """
    Custom Exception handler;
    example: raise APIValidation("", status_code=404)
    """
    status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
    default_detail = 'Service temporarily unavailable, try again later.'
    default_code = 'error'

    def __init__(self, detail=default_detail, code=default_code, status_code=status_code):
        self.status_code = status_code
        super().__init__(detail, code)


def uni_exception_handler(exc, context):
    response = exception_handler(exc, context)
    return response
