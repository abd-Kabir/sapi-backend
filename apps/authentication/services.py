import calendar
import logging
from datetime import timedelta, date

from django.db.models import Sum, Q, Count
from django.db.models.functions import TruncDate, TruncWeek, TruncMonth, TruncYear
from django.utils.timezone import now
from django.utils.translation import gettext_lazy as _
from rest_framework_simplejwt.tokens import RefreshToken

from apps.authentication.models import UserActivity, User, UserSubscription, BlockedUser, Donation, SubscriptionPlan
from apps.content.models import Post, Comment
from apps.integrations.api_integrations.firebase import send_notification_to_user
from apps.integrations.models import MultibankTransaction
from apps.integrations.services.multibank import multibank_payment
from config.core.api_exceptions import APIValidation

logger = logging.getLogger(__name__)


def generate_date_range(group, period, queryset):
    period_days = {
        'day': 1,
        'week': 7,
        'month': 30,
        'year': 365
    }
    date_objects = []
    last_day = now()
    first_day = last_day - timedelta(days=period_days[period])
    if group == 'day':
        grouped_data = (
            queryset
            .filter(date_joined__date__gte=first_day, date_joined__date__lte=last_day)
            .annotate(day=TruncDate('date_joined'))
            .values('day')
            .annotate(count=Count('id'))
            .order_by('day')
        )
        count_map = {item['day']: item['count'] for item in grouped_data}

        for day in range((last_day - first_day).days + 1):
            that_day = first_day + timedelta(days=day)
            date_objects.append({
                'date': that_day.strftime('%Y-%m-%d'),
                'count': count_map.get((first_day + timedelta(days=day)).date(), 0)
            })
    elif group == 'week':
        first_week_start = first_day - timedelta(days=first_day.weekday())
        last_week_start = last_day - timedelta(days=last_day.weekday())

        grouped_data = (
            queryset
            .filter(date_joined__date__gte=first_week_start, date_joined__date__lte=last_day)
            .annotate(week=TruncWeek('date_joined'))
            .values('week')
            .annotate(count=Count('id'))
            .order_by('week')
        )
        count_map = {item['week'].date(): item['count'] for item in grouped_data}

        week_count = ((last_week_start - first_week_start).days // 7) + 1
        for i in range(week_count):
            week_start = first_week_start + timedelta(weeks=i)
            date_objects.append({
                'date': week_start.strftime('%Y-%m-%d'),
                'count': count_map.get(week_start.date(), 0)
            })
    elif group == 'month':
        first_month_start = first_day.replace(day=1)
        last_month_start = last_day.replace(day=1)

        grouped_data = (
            queryset
            .filter(date_joined__date__gte=first_month_start, date_joined__date__lte=last_day)
            .annotate(month=TruncMonth('date_joined'))
            .values('month')
            .annotate(count=Count('id'))
            .order_by('month')
        )
        count_map = {item['month'].date(): item['count'] for item in grouped_data}

        # Generate month list from first_month_start to last_month_start
        current = first_month_start
        while current <= last_month_start:
            date_objects.append({
                'date': current.strftime('%Y-%m-%d'),
                'count': count_map.get(current.date(), 0)
            })
            if current.month == 12:
                current = current.replace(year=current.year + 1, month=1)
            else:
                current = current.replace(month=current.month + 1)
    elif group == 'year':
        first_year_start = first_day.replace(month=1, day=1)
        last_year_start = last_day.replace(month=1, day=1)

        grouped_data = (
            queryset
            .filter(date_joined__date__gte=first_year_start, date_joined__date__lte=last_day)
            .annotate(year=TruncYear('date_joined'))
            .values('year')
            .annotate(count=Count('id'))
            .order_by('year')
        )
        count_map = {item['year'].date(): item['count'] for item in grouped_data}

        current = first_year_start
        while current <= last_year_start:
            date_objects.append({
                'date': current.strftime('%Y-%m-%d'),
                'count': count_map.get(current.date(), 0)
            })
            current = current.replace(year=current.year + 1)
    return date_objects


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


def creator_earnings(period: str = 'month'):
    periods = {
        'day': timedelta(days=1),
        'week': timedelta(days=7),
        'month': timedelta(days=30),
        'year': timedelta(days=365)
    }

    today = now()
    earnings = (
        MultibankTransaction.objects
        .filter(status='paid', created_at__gte=today - periods[period])
        .aggregate(creator_earnings=Sum('creator_amount'))
        .get('creator_earnings', 0)
    )
    return {'data': earnings}


def registered_accounts(group, period, user_type='all', start_date=None, end_date=None, is_active=True):
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
    user_objects = user_objects.filter(
        user_filter,
        start_date_filter,
        end_date_filter,
        is_deleted=False
    )

    response = generate_date_range(group, period, user_objects)
    return response

    # accounts_data = user_objects.filter(
    #     user_filter,
    #     start_date_filter,
    #     end_date_filter,
    #     is_deleted=False
    # ).annotate(
    #     period=trunc_func('date_joined')
    # ).values('period').annotate(
    #     count=Count('id')
    # ).order_by('period')
    #
    # return {
    #     'data': [
    #         {
    #             'date': item['period'].strftime('%Y-%m-%d'),
    #             'count': item['count']
    #         }
    #         for item in accounts_data
    #     ]
    # }


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


def send_notification_to_users(users, title, text):
    for user in users:
        send_notification_to_user(user, title, text)


def resubscribe(user):
    subscriptions = UserSubscription.objects.filter(
        subscriber=user,
        is_active=True,
        end_date__lt=now(),
        one_time=False,
    )
    for subscription in subscriptions:
        try:
            plan = subscription.plan
            creator = subscription.creator

            if not plan:
                logger.warning(f"No duration found for plan {plan} in subscription {subscription.id}")
                continue

            if BlockedUser.is_blocked(creator, user):
                subscription.is_active = False
                subscription.save(update_fields=['is_active'])
                continue

            multibank_payment(
                user=user,
                creator=creator,
                card=subscription.subscriber_card,
                amount=plan.price,
                payment_type='subscription',
                commission_by_subscriber=subscription.commission_by_subscriber,
            )
            if plan.duration:
                subscription.end_date = now() + plan.duration
            else:
                today = date.today()
                days_in_month = calendar.monthrange(today.year, today.month)[1]
                subscription.end_date = now() + timedelta(days=days_in_month)
            subscription.save(update_fields=['end_date'])
        except Exception as e:
            logger.error(f"Resubscribe failed for subscription {subscription.id}: {str(e)}")
            continue


def get_extra_text(obj):
    if not obj.content_id:
        return None

    if obj.type == 'donation':
        try:
            donation = Donation.objects.get(id=obj.content_id)
            return {
                'amount': donation.amount,
                'message': donation.message
            }
        except Donation.DoesNotExist:
            return None

    elif obj.type == 'commented':
        try:
            comment = Comment.objects.get(id=obj.content_id)
            return {
                'message': comment.text,
            }
        except Comment.DoesNotExist:
            return None

    elif obj.type == 'subscribed':
        try:
            subscribed = SubscriptionPlan.objects.get(id=obj.content_id)
            user_sub = (
                UserSubscription.objects.filter(
                    creator=obj.content_owner,
                    subscriber=obj.initiator,
                    is_active=True
                ).exists()
            )
            if user_sub:
                return {
                    'message': subscribed.name,
                    'amount': subscribed.price,
                }
            return None
        except SubscriptionPlan.DoesNotExist:
            return None

    return None


def get_operation_history(obj):
    if not obj.content_id:
        return None
    if obj.type == 'donation':
        try:
            donation = Donation.objects.get(id=obj.content_id)
            return {
                'amount': donation.amount,
                'message': donation.message
            }
        except Donation.DoesNotExist:
            return None
    elif obj.type == 'subscribed':
        try:
            subscribed = SubscriptionPlan.objects.get(id=obj.content_id)
            user_sub = (
                UserSubscription.objects.filter(
                    creator=obj.content_owner,
                    subscriber=obj.initiator,
                    is_active=True
                ).exists()
            )
            if user_sub:
                return {
                    'message': subscribed.name,
                    'amount': subscribed.price,
                }
            return None
        except SubscriptionPlan.DoesNotExist:
            return None
    return None
