# from django.dispatch import receiver
# from django.contrib.auth.signals import user_logged_in
# from cart.models import Cart

# @receiver(user_logged_in)
# def create_cart_if_not_exists(sender, user, request, **kwargs):
#     if not Cart.objects.filter(user=user).exists():
#         Cart.objects.create(user=user)
