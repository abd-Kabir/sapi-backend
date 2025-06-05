from drf_yasg.utils import swagger_auto_schema
from django.utils.translation import gettext_lazy as _
from rest_framework.generics import ListAPIView, RetrieveAPIView
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.authentication.models import User
from apps.authentication.serializers.admin import AdminCreatorListSerializer, AdminCreatorUpdateSAPIShareSerializer
from config.core.api_exceptions import APIValidation


class AdminCreatorListAPIView(ListAPIView):
    queryset = User.objects.filter(is_creator=True)
    serializer_class = AdminCreatorListSerializer


class AdminCreatorRetrieveAPIView(RetrieveAPIView):
    queryset = User.objects.filter(is_creator=True)
    serializer_class = AdminCreatorListSerializer


class AdminCreatorSAPIShareAPIView(APIView):
    response_serializer_class = AdminCreatorListSerializer
    serializer_class = AdminCreatorUpdateSAPIShareSerializer

    @staticmethod
    def get_creator(pk):
        try:
            return User.objects.get(pk=pk, is_creator=True)
        except:
            raise APIValidation(_('Контент креатор не найден'), status_code=404)

    @swagger_auto_schema(request_body=AdminCreatorUpdateSAPIShareSerializer,
                         responses={200: AdminCreatorListSerializer()})
    def patch(self, request, pk, *args, **kwargs):
        serializer = self.serializer_class(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        creator = self.get_creator(pk)

        creator.sapi_share = data.get('sapi_share')
        creator.save(update_fields=['sapi_share'])
        response = self.response_serializer_class(creator).data
        return Response(response)
