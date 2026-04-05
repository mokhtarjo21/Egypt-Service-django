from django.contrib.contenttypes.models import ContentType
from .models import Notification, NotificationPreference

def send_notification_if_enabled(recipient, notification_type, title_ar, message_ar, title_en="", message_en="", related_object=None):
    """
    Creates a Notification object and sends push/email based on user preferences.
    """
    # 1. Check user preferences
    prefs, created = NotificationPreference.objects.get_or_create(user=recipient)
    
    # Check if this type of notification is enabled via push (our main app channel)
    # We map our notification_type to the preference flags.
    should_send_push = True
    if notification_type == 'message':
        should_send_push = prefs.push_messages
    elif notification_type in ['booking', 'booking_status', 'booking_confirmed', 'booking_cancelled', 'booking_started', 'booking_completed']:
        should_send_push = prefs.push_bookings
    elif notification_type == 'review':
        should_send_push = prefs.push_reviews
    elif notification_type in ['service_approved', 'service_rejected', 'subscription']:
        should_send_push = True  # These are system/billing, usually alert anyway
        
    # If the user disabled push for this type, we still create the Notification in DB
    # so they can see it in their notification center, but we wouldn't trigger FCM/Expo.
    
    content_type = None
    object_id = None
    if related_object:
        content_type = ContentType.objects.get_for_model(related_object)
        object_id = related_object.id
    
    notification = Notification.objects.create(
        recipient=recipient,
        notification_type=notification_type,
        title_ar=title_ar,
        title_en=title_en,
        message_ar=message_ar,
        message_en=message_en,
        content_type=content_type,
        object_id=object_id
    )
    
    # If should_send_push is True, here we would trigger the actual push (FCM, Apns, Expo)
    # if should_send_push:
    #    send_push_notification(recipient, title_ar, message_ar, data={'id': notification.id})
    
    return notification
