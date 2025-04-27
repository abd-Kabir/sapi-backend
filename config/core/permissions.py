from rest_framework import permissions


class IsCreator(permissions.BasePermission):
    """
    Allow to creators
    """

    def has_permission(self, request, view):
        user = request.user
        if user.is_creator and user.is_authenticated:
            return True
        return False
