from rest_framework import permissions

from accounts.models import User
from utilities.statics import ROLE_ADMIN, ROLE_MANAGER, ROLE_CASHIER


class IsSuperUser(permissions.BasePermission):
    """
    Check if user is superuser
    """
    message = 'Only superadmin is allowed'

    def has_permission(self, request, view):
        return request.user.is_superuser

class IsOwner(permissions.BasePermission):
    
    def has_object_permission(self, request, view, obj):
        if isinstance(obj, User):
            return obj.id == request.user.id
        elif hasattr(obj, 'user'):
            return obj.user == request.user
        return False
        


class IsCompanyAdmin(permissions.BasePermission):
    """
    Check if user is company admin
    """
    message = 'Only admin is allowed'

    def has_permission(self, request, view):

        company_pk = view.kwargs.get('company_pk', None)
        
        if request.user.is_anonymous: 
            return False

        if company_pk: 
            return request.user.company_roles.filter(is_active=True, company_id= company_pk, role_id=ROLE_ADMIN).exists()
        return False
    

    def has_object_permission(self, request, view, obj): 
        company_pk = view.kwargs.get('company_pk', None)
        return obj.company_id ==  company_pk


class IsCompanyManager(permissions.BasePermission):
    """
    Check if user is company manager
    """
    message = 'Only manager is allowed'

    def has_permission(self, request, view):

        company_pk = view.kwargs.get('company_pk', None)
        
        if request.user.is_anonymous: 
            return False

        if company_pk: 
            return request.user.company_roles.filter(is_active=True, company_id= company_pk, role_id=ROLE_MANAGER).exists()
        return False

    def has_object_permission(self, request, view, obj): 
        company_pk = view.kwargs.get('company_pk', None)
        return obj.company_id ==  company_pk


class IsCompanyCashier(permissions.BasePermission):
    """
    Check if user is company Cashier
    """
    message = 'Only cashier is allowed'

    def has_permission(self, request, view):

        company_pk = view.kwargs.get('company_pk', None)
        
        if request.user.is_anonymous: 
            return False

        if company_pk: 
            return request.user.company_roles.filter(is_active=True, company_id= company_pk, role_id=ROLE_CASHIER).exists()
        return False

    def has_object_permission(self, request, view, obj): 
        company_pk = view.kwargs.get('company_pk', None)
        return obj.company_id ==  company_pk


class ReadOnly(permissions.BasePermission):
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True

        # Write permissions are only allowed to the owner
        # return obj.user == request.user



def has_dashboard_access(user): 
    return user.company_roles.filter(is_active=True).exists() or (user.is_staff and user.is_active)

