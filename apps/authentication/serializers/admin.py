from django.db.models import Sum
from rest_framework import serializers, status
from django.utils.translation import gettext_lazy as _

from apps.authentication.models import User, NotificationDistribution, NotifDisStatus
from apps.authentication.tasks import send_notification_task
from apps.content.models import ReportTypes, Report, ReportComment
from apps.files.serializers import FileSerializer
from apps.integrations.api_integrations.firebase import send_notification_to_user
from config.core.api_exceptions import APIValidation


class AdminCreatorListSerializer(serializers.ModelSerializer):
    subscribers_count = serializers.SerializerMethodField(allow_null=True)
    followers_count = serializers.SerializerMethodField(allow_null=True)
    status = serializers.SerializerMethodField(allow_null=True)
    username = serializers.SerializerMethodField(allow_null=True)
    phone_number = serializers.SerializerMethodField(allow_null=True)

    profile_photo_info = FileSerializer(read_only=True, allow_null=True, source='profile_photo')
    profile_banner_photo_info = FileSerializer(read_only=True, allow_null=True, source='profile_banner_photo')
    category_name = serializers.CharField(source='category.name', read_only=True, allow_null=True)
    block_reason_display = serializers.CharField(source='get_block_reason_display', read_only=True, allow_null=True)

    @staticmethod
    def get_subscribers_count(obj):
        return obj.subscribers_count()

    @staticmethod
    def get_followers_count(obj):
        return obj.followers_count()

    @staticmethod
    def get_status(obj):
        if obj.is_blocked_by:
            status = _('Заблокирован')
        else:
            status = _('Активен') if obj.is_creator else _('Не активен')
        return status

    @staticmethod
    def get_username(obj):
        return obj.username if obj.username else obj.temp_username

    @staticmethod
    def get_phone_number(obj):
        return obj.phone_number if obj.phone_number else obj.temp_phone_number

    class Meta:
        model = User
        fields = [
            'id',
            'username',
            'phone_number',
            'subscribers_count',
            'followers_count',
            'sapi_share',
            'date_joined',
            'status',
            'block_reason',
            'block_reason_display',

            'profile_photo_info',
            'profile_banner_photo_info',
            'category_name',
        ]


class AdminCreatorRetrieveSerializer(serializers.ModelSerializer):
    first_content = serializers.SerializerMethodField(allow_null=True)
    payment_data = serializers.SerializerMethodField(allow_null=True)

    subscribers_count = serializers.SerializerMethodField(allow_null=True)
    followers_count = serializers.SerializerMethodField(allow_null=True)
    earned = serializers.SerializerMethodField(allow_null=True)
    status = serializers.SerializerMethodField(allow_null=True)
    block_reason_display = serializers.CharField(source='get_block_reason_display', allow_null=True)
    username = serializers.SerializerMethodField(allow_null=True)
    phone_number = serializers.SerializerMethodField(allow_null=True)

    profile_photo_info = FileSerializer(read_only=True, allow_null=True, source='profile_photo')
    profile_banner_photo_info = FileSerializer(read_only=True, allow_null=True, source='profile_banner_photo')
    category_name = serializers.CharField(source='category.name', read_only=True, allow_null=True)

    @staticmethod
    def get_first_content(obj):
        return obj.posts.exists()

    @staticmethod
    def get_payment_data(obj):
        return obj.cards.filter(is_active=True).exists()

    @staticmethod
    def get_subscribers_count(obj):
        return obj.subscribers_count()

    @staticmethod
    def get_followers_count(obj):
        return obj.followers_count()

    @staticmethod
    def get_earned(obj):
        return obj.creator_multibank_transactions.filter(status='paid').aggregate(earned=Sum('amount'))['earned']

    @staticmethod
    def get_status(obj):
        if obj.is_blocked_by:
            status = _('Заблокирован')
        else:
            status = _('Активен') if obj.is_creator else _('Не активен')
        return status

    @staticmethod
    def get_username(obj):
        return obj.username if obj.username else obj.temp_username

    @staticmethod
    def get_phone_number(obj):
        return obj.phone_number if obj.phone_number else obj.temp_phone_number

    class Meta:
        model = User
        fields = [
            'id',
            'username',
            'phone_number',
            'sapi_share',
            'date_joined',

            'first_content',
            'payment_data',

            'subscribers_count',
            'followers_count',
            'earned',
            'status',
            'multibank_verified',
            'multibank_account',
            'block_reason',
            'block_reason_display',
            'block_desc',

            'profile_photo_info',
            'profile_banner_photo_info',
            'category_name',
        ]


class AdminBlockCreatorPostSerializer(serializers.Serializer):
    user_id = serializers.IntegerField(required=False)
    post_id = serializers.IntegerField(required=False)
    report_id = serializers.IntegerField(required=False)
    block_reason = serializers.ChoiceField(choices=ReportTypes.choices)
    block_desc = serializers.CharField(required=False)

    def validate(self, attrs):
        if not attrs.get('user_id') and not attrs.get('post_id'):
            raise APIValidation(_('Отправьте ID юзера или поста'), status_code=status.HTTP_400_BAD_REQUEST)
        return super().validate(attrs)


class AdminUnblockCreatorPostSerializer(serializers.Serializer):
    user_id = serializers.IntegerField(required=False)
    post_id = serializers.IntegerField(required=False)

    def validate(self, attrs):
        if not attrs.get('user_id') and not attrs.get('post_id'):
            raise APIValidation(_('Отправьте ID юзера или поста'), status_code=status.HTTP_400_BAD_REQUEST)
        return attrs


class AdminCreatorUpdateSAPIShareSerializer(serializers.Serializer):
    sapi_share = serializers.IntegerField()


class ReportListSerializer(serializers.ModelSerializer):
    post_files = FileSerializer(source='post.files', read_only=True, allow_null=True, many=True)
    post_username = serializers.CharField(source='post.user.username', read_only=True)
    post_title = serializers.CharField(source='post.title', read_only=True)
    post_description = serializers.CharField(source='post.description', read_only=True)
    report_user = serializers.CharField(source='report_user.username', read_only=True)
    report_user_description = serializers.CharField(source='report_user.creator_description', read_only=True)
    reported_username = serializers.CharField(source='user.username', read_only=True)
    report_type_display = serializers.CharField(source='get_report_type_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    category_name = serializers.CharField(source='post.category.name', read_only=True)

    class Meta:
        model = Report
        fields = [
            'id',
            'category_name',
            'post',
            'post_files',
            'post_username',
            'post_title',
            'post_description',
            'report_user',
            'report_user_description',
            'report_type',
            'description',
            'is_resolved',
            'resolved_at',
            'resolved_by',
            'status_display',
            'reported_username',
            'report_type_display',
            'created_at',
        ]
        read_only_fields = [
            'id',
            'is_resolved',
            'resolved_at',
            'resolved_by',
            'user'
        ]

    def create(self, validated_data):
        # Automatically set the user from the request
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)


class ReportRetrieveSerializer(serializers.ModelSerializer):
    creator = serializers.SerializerMethodField()
    post_uploaded_at = serializers.DateTimeField(source='post.created_at', read_only=True, allow_null=True)
    post_title = serializers.CharField(source='post.title', read_only=True, allow_null=True)
    post_description = serializers.CharField(source='post.description', read_only=True, allow_null=True)
    post_files = FileSerializer(source='post.files', many=True, read_only=True, allow_null=True)
    post_type = serializers.CharField(source='post.post_type', read_only=True, allow_null=True)
    post_type_display = serializers.CharField(source='post.get_post_type_display', read_only=True, allow_null=True)
    report_user = serializers.CharField(source='report_user.username', read_only=True)
    report_user_description = serializers.CharField(source='report_user.creator_description', read_only=True)

    reporter = serializers.SerializerMethodField()
    report_type_display = serializers.CharField(source='get_report_type_display', read_only=True)
    report_description = serializers.CharField(source='description', read_only=True)
    report_created_at = serializers.DateTimeField(source='created_at', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    admin_comments = serializers.SerializerMethodField()

    class Meta:
        model = Report
        fields = [
            'creator',
            'post_uploaded_at',
            'post_title',
            'post_description',
            'post_files',
            'post_type',
            'post_type_display',
            'report_user',
            'report_user_description',

            'reporter',
            'report_type',
            'report_type_display',
            'report_description',
            'report_created_at',
            'status',
            'status_display',

            'admin_comments',
        ]

    def get_creator(self, obj):
        if obj.post:
            user = obj.post.user
        elif obj.report_user:
            user = obj.report_user
        else:
            return None
        return {
            "id": user.id,
            "username": user.username,
            "profile_photo": FileSerializer(user.profile_photo).data if user.profile_photo else None
        }

    def get_reporter(self, obj):
        user = obj.user
        return {
            "id": user.id,
            "username": user.username,
            "profile_photo": FileSerializer(user.profile_photo).data if user.profile_photo else None
        }

    def get_admin_comments(self, obj):
        comments = ReportComment.objects.filter(report=obj).order_by('created_at')
        return [
            {
                "username": c.user.username,
                "text": c.text,
                "created_at": c.created_at.strftime('%d %B, %Y')
            }
            for c in comments
        ]


class AdminNotifDisSerializer(serializers.ModelSerializer):
    created_at = serializers.DateTimeField(read_only=True)
    status = serializers.ChoiceField(choices=NotifDisStatus.choices, read_only=True)

    @staticmethod
    def get_users(user_type):
        if user_type == 'creators':
            return User.objects.filter(is_creator=True)
        elif user_type == 'users':
            return User.objects.filter(is_creator=False)
        elif user_type == 'all':
            return User.objects.all()
        else:
            raise APIValidation(_('Тип юзера неправильный'), status_code=status.HTTP_400_BAD_REQUEST)

    def manipulate_notification_sending(self, instance):
        validated_data = self.validated_data
        if not validated_data.get('sending_date') and not instance.is_draft:
            if validated_data.get('types'):
                for notif_type in validated_data.get('types', []):
                    if notif_type == 'push_notification':
                        users = self.get_users(validated_data.get('user_type'))
                        user_ids = list(users.values_list('id', flat=True))
                        send_notification_task.delay(
                            user_ids,
                            validated_data.get('title_ru'),
                            validated_data.get('text_ru'),
                            instance.id
                        )
            instance.status = 'sent'
        else:
            if validated_data.get('types') and not instance.is_draft:
                for notif_type in validated_data.get('types', []):
                    if notif_type == 'push_notification':
                        users = self.get_users(validated_data.get('user_type'))
                        user_ids = list(users.values_list('id', flat=True))
                        send_notification_task.apply_async(
                            args=(
                                user_ids,
                                validated_data.get('title_ru'),
                                validated_data.get('text_ru'),
                                instance.id
                            ),
                            eta=validated_data.get('sending_date')
                        )
                instance.status = 'waiting'
                instance.save()

    def create(self, validated_data):
        instance = super().create(validated_data)
        if validated_data.get('is_draft'):
            instance.status = 'draft'
            instance.save()
            return instance
        self.manipulate_notification_sending(instance)
        instance.save()
        return instance

    def update(self, instance: NotificationDistribution, validated_data):
        if not instance.is_draft:
            raise APIValidation(_('Можете обновлять только со статусом драфт'), status_code=status.HTTP_400_BAD_REQUEST)
        instance = super().update(instance, validated_data)
        if not instance.is_draft:
            instance.status = 'waiting'
        self.manipulate_notification_sending(instance)
        instance.save()
        return instance

    class Meta:
        model = NotificationDistribution
        fields = [
            'id',
            'is_draft',
            'created_at',
            'title_ru',
            'title_uz',
            'text_ru',
            'text_uz',
            'status',
            'types',
            'user_type',
            'sending_date',
        ]
