from rest_framework import permissions


class AllowGet(permissions.BasePermission):
    """
    Allow users to GET requests
    """

    def has_permission(self, request, view):
        if view.action == 'list' or view.action == 'retrieve':
            return True
        return request.user.is_authenticated


class IsCreator(permissions.BasePermission):
    """
    Allow to creators
    """

    def has_permission(self, request, view):
        user = request.user
        if user.is_authenticated and user.is_creator:
            return True
        return False


class IsAdmin(permissions.BasePermission):
    """
    Allow to admins
    """

    actions_tool = {
        'list': 'VIEW',
        'retrieve': 'VIEW',
        'create': 'MODIFY',
        'update': 'MODIFY',
        'partial_update': 'MODIFY',
        'destroy': 'MODIFY',
    }

    def has_permission(self, request, view):
        user = request.user
        if user.is_authenticated and user.is_admin:
            available_permissions = user.permissions.values_list('permission', flat=True)
            action_code = view.get_action()
            action = self.actions_tool[action_code]

            router_names = view.router_name.split('_')
            for router_name in router_names:
                if f'MODIFY_{router_name}' in available_permissions:
                    return True
                needed_role = f'{action}_{router_name}'
                return needed_role in available_permissions
        return False


class IsAdminAllowGet(permissions.BasePermission):
    """
    Allow to admins and get requests
    """

    actions_tool = {
        'list': 'VIEW',
        'retrieve': 'VIEW',
        'create': 'MODIFY',
        'update': 'MODIFY',
        'partial_update': 'MODIFY',
        'destroy': 'MODIFY',
    }

    def has_permission(self, request, view):
        if view.action == 'list' or view.action == 'retrieve':
            return True
        user = request.user
        if user.is_authenticated and user.is_admin:
            available_permissions = user.permissions.values_list('permission', flat=True)
            action_code = view.get_action()
            action = self.actions_tool[action_code]

            router_names = view.router_name.split('_')
            for router_name in router_names:
                if f'MODIFY_{router_name}' in available_permissions:
                    return True
                needed_role = f'{action}_{router_name}'
                return needed_role in available_permissions
        return False
