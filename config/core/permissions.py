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

    def has_permission(self, request, view):
        user = request.user
        if user.groups.filter(name='ADMIN').exists():
            return True
        return False


class IsAdminAllowGet(permissions.BasePermission):
    """
    Allow to admins and get requests
    """

    def has_permission(self, request, view):
        if view.action == 'list' or view.action == 'retrieve':
            return True
        user = request.user
        if user.groups.filter(name='ADMIN').exists():
            return True
        return False
