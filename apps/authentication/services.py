from datetime import timedelta

from django.db.models import Sum, Q, Count
from django.utils.timezone import now
from django.utils.translation import gettext_lazy as _
from rest_framework_simplejwt.tokens import RefreshToken

from apps.authentication.models import UserActivity, User, UserSubscription
from apps.content.models import Post
from apps.integrations.models import MultibankTransaction
from config.core.api_exceptions import APIValidation


def create_activity(activity_type: str, content: str, content_id: str | int, initiator, content_owner):
    """
    types: donation, commented, followed, subscribed, liked
    """
    UserActivity.objects.create(
        type=activity_type,
        content=content,
        content_id=content_id,
        initiator=initiator,
        content_owner=content_owner,
    )


def get_last_week_days():
    today = now().date()
    return [(today - timedelta(days=i)) for i in reversed(range(7))]


def get_last_month_intervals():
    today = now().date()
    return [(today - timedelta(days=30)) + timedelta(days=i * 5) for i in range(7)]


def permissions_by_category(permissions):
    categories = set({'_'.join(i.split('_')[1:]) for i in permissions})
    categories = {i: [] for i in categories}
    for permission in permissions:
        category_part = '_'.join(permission.split('_')[1:])
        categories[category_part].append(permission)
    return categories


def authenticate_user(request):
    phone_number = request.data.get('phone_number')
    password = request.data.get('password')

    try:
        user = User.objects.get(phone_number=phone_number)
        if user.check_password(password) and user.is_admin:
            refresh = RefreshToken.for_user(user)
            permissions = list(user.permissions.values_list('permission', flat=True))
            return {
                'refresh': str(refresh),
                'access': str(refresh.access_token),
                'permissions': permissions,
                'permissions_by_category': permissions_by_category(permissions),
            }
    except User.DoesNotExist:
        pass

    raise APIValidation(_('Неправильный логин или пароль'), status_code=403)


def creator_earnings():
    earnings = (
        MultibankTransaction.objects
        .filter(status='paid')
        .aggregate(creator_earnings=Sum('creator_amount'))
        .get('creator_earnings', 0)
    )
    return {'data': earnings}


def registered_accounts(trunc_func, user_type='all', start_date=None, end_date=None, is_active=True):
    user_filter = Q()
    start_date_filter = Q()
    end_date_filter = Q()
    if user_type == 'creators':
        user_filter = Q(is_creator=True)
    elif user_type == 'users':
        user_filter = Q(is_creator=False)
    if start_date:
        start_date_filter = Q(date_joined__date__gte=start_date)
    if end_date:
        end_date_filter = Q(date_joined__date__lte=end_date)

    user_objects = User.objects
    if not is_active:
        user_objects = User.all_objects
    accounts_data = user_objects.filter(
        user_filter,
        start_date_filter,
        end_date_filter,
        is_deleted=False
    ).annotate(
        period=trunc_func('date_joined')
    ).values('period').annotate(
        count=Count('id')
    ).order_by('period')

    return {
        'data': [
            {
                'date': item['period'].strftime('%Y-%m-%d'),
                'count': item['count']
            }
            for item in accounts_data
        ]
    }


def active_subscriptions(trunc_func, start_date=None, end_date=None):
    start_date_filter = Q()
    end_date_filter = Q()
    if start_date:
        start_date_filter = Q(created_at__date__gte=start_date)
    if end_date:
        end_date_filter = Q(created_at__date__lte=end_date)
    subs_data = UserSubscription.objects.filter(
        start_date_filter,
        end_date_filter,
        is_active=True,
        end_date__date__gte=now(),
    ).annotate(
        period=trunc_func('created_at')
    ).values('period').annotate(
        count=Count('id')
    ).order_by('period')
    return {
        'data': [
            {
                'date': item['period'].strftime('%Y-%m-%d'),
                'count': item['count']
            }
            for item in subs_data
        ]
    }


def content_type_counts():
    content_types_data = Post.objects.filter(
        is_deleted=False
    ).values('post_type').annotate(
        count=Count('id')
    ).order_by('-count')

    # Map post types to Russian names as shown in screenshot
    type_names = {
        'video': 'Видео',
        'image': 'Изображения',
        'music': 'Музыка',
        'text': 'Текстовые посты',
        'poll': 'Опросы',
        'live': 'Прямые эфиры'
    }

    return {
        'data': [
            {
                'type': type_names.get(item['post_type'], item['post_type']),
                'count': item['count']
            }
            for item in content_types_data
        ]
    }


def platform_earnings(trunc_func, start_date=None, end_date=None):
    start_date_filter = Q()
    end_date_filter = Q()
    if start_date:
        start_date_filter = Q(created_at__date__gte=start_date)
    if end_date:
        end_date_filter = Q(created_at__date__lte=end_date)
    revenue_data = MultibankTransaction.objects.filter(
        start_date_filter,
        end_date_filter,
        status='paid'
    ).annotate(
        period=trunc_func('created_at')
    ).values('period').annotate(
        total_revenue=Sum('sapi_amount')
    ).order_by('period')

    # Calculate total revenue
    total_revenue = MultibankTransaction.objects.filter(
        start_date_filter,
        end_date_filter,
        status='paid'
    ).aggregate(total=Sum('sapi_amount'))['total'] or 0

    return {
        'total_amount': total_revenue,
        'data': [
            {
                'date': item['period'].strftime('%Y-%m-%d'),
                'amount': item['total_revenue'] or 0
            }
            for item in revenue_data
        ]
    }
