from django.urls import path, include
from rest_framework.routers import DefaultRouter

from . import views

router = DefaultRouter()
router.register(r'organizations', views.OrganizationViewSet, basename='organizations')
router.register(r'members', views.OrganizationMemberViewSet, basename='members')

app_name = 'teams'

urlpatterns = [
    path('', include(router.urls)),
    path('invites/', views.OrganizationInviteView.as_view(), name='organization-invites'),
    path('invites/<uuid:invite_id>/accept/', views.AcceptInviteView.as_view(), name='accept-invite'),
]