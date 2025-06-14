from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from .models import *
from users.models import User
from products.models import Product
import copy
from django.http import JsonResponse
import json

class RateAPIView(APIView):
    def post(self, request):
        rate = request.data.get('rate')
        content = request.data.get('content')
        user = request.user
        product_id = request.data.get('id')
        if Rating.objects.filter(user=user.id,product=product_id ).exists():
            current_rete = Rating.objects.get(user=user.id,product=product_id )
            current_rete.value = rate
            current_rete.content=content
            current_rete.save()
        else :
            product = Product.objects.get(id=product_id)
            new_rate = Rating.objects.create(
                user=user,
                product=product,
                value=rate,
                content=content
            )

        rates = Rating.objects.filter(product=product_id)
        if not rates:
            return JsonResponse([], safe=False, status=status.HTTP_200_OK)
        rate_list = []
        for rate in rates:
            user_profile = User.objects.get(id=rate.user.id)
            rate_list.append({
                'id': rate.id,
                'first_name': user_profile.first_name,
                'user_photo': user_profile.picture.url,
                'rate': rate.value,
                'content':rate.content
            })
       
        return JsonResponse(rate_list, safe=False, status=status.HTTP_200_OK)
    def get(self, request, slug):
        print(slug, 'slug')
        rates = Rating.objects.filter(product=slug)
        if not rates:
            return JsonResponse([], safe=False, status=status.HTTP_200_OK)
        rate_list = []
        for rate in rates:
            user_profile = User.objects.get(id=rate.user.id)
            rate_list.append({
                'id': rate.id,
                'first_name': user_profile.first_name,
                'user_photo': user_profile.picture.url,
                'rate': rate.value,
                'content':rate.content
            })
       
        return JsonResponse(rate_list, safe=False, status=status.HTTP_200_OK)
