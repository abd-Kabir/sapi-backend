import logging

logger = logging.getLogger('request_logger')


class RequestLogMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Read and decode request body safely
        try:
            body = request.body.decode('utf-8')
        except Exception:
            body = '[Unreadable Body]'

        logger.info(f'{request.method} {request.path} - Body: {body}')

        response = self.get_response(request)
        return response
