from drf_yasg import openapi

chat_settings_swagger = {
            200: openapi.Response(
                description='List of chat settings. Can chat choices: subscribers, donations, everyone, nobody;',
                schema=openapi.Schema(
                    type=openapi.TYPE_ARRAY,
                    items=openapi.Schema(
                        type=openapi.TYPE_OBJECT,
                        properties={
                            'id': openapi.Schema(type=openapi.TYPE_INTEGER),
                            'can_chat': openapi.Schema(type=openapi.TYPE_STRING),
                            'subscription_plans': openapi.Schema(
                                type=openapi.TYPE_ARRAY,
                                items=openapi.Items(type=openapi.TYPE_INTEGER),
                                description='Only present when can_chat is "subscribers"',
                            ),
                            'minimum_message_donation': openapi.Schema(
                                type=openapi.TYPE_INTEGER,
                                description='Only present when can_chat is "donations"',
                            ),
                        },
                        required=['id', 'can_chat']
                    )
                ),
                examples={
                    'application/json': [
                        {'id': 2, 'can_chat': 'subscribers', 'subscription_plans': [1, 2]},
                        {'id': 3, 'can_chat': 'donations', 'minimum_message_donation': 20000},
                        {'id': 4, 'can_chat': 'everyone'},
                        {'id': 5, 'can_chat': 'nobody'}
                    ]
                }
            )
        }