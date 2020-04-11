from .views import *
from django.urls import include, path

urlpatterns = [
    path(
        'radius_renew/<token_value>',
        renew_radius_password,
        name='renew-radius-password',
    ),

    path('', login, name="guest_login"),
    path('logout', logout, name="guest_logout"),
    path('home', home, name="home"),
    path('change_password/<radcheck_id>', change_password, name="change_password"),
    path('reset_password', reset_password, name="reset_password"),
    path('datatable_data', datatable_data, name="datatable_data")

]
