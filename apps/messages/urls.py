from django.urls import path, include
from rest_framework.routers import DefaultRouter

from . import views

# router = DefaultRouter()
# router.register(r'conversations', views.ConversationViewSet)
# router.register(r'messages', views.MessageViewSet)
router = DefaultRouter()
router.register(r'conversations', views.ConversationViewSet, basename='conversation')
router.register(r'messages', views.MessageViewSet, basename='message')

app_name = 'messages'

urlpatterns = [
    path('', include(router.urls)),
]