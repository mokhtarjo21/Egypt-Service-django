"""
Views for the reviews app.
"""

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny

from .models import Review, ReviewHelpfulness
from .serializers import ReviewSerializer, ReviewHelpfulnessSerializer
from apps.notifications.utils import send_notification_if_enabled


class ReviewViewSet(viewsets.ModelViewSet):
    """
    ViewSet for reviews.
    """
    queryset = Review.objects.all()#filter(is_active=True, status='approved')
    serializer_class = ReviewSerializer
    permission_classes = [IsAuthenticated]

    def get_permissions(self):
        if self.action == 'list':
            permission_classes = [AllowAny]
        else:
            permission_classes = [IsAuthenticated]
        return [permission() for permission in permission_classes]

    def perform_create(self, serializer):
        review = serializer.save(reviewer=self.request.user)
        
        # Notify provider
        send_notification_if_enabled(
            recipient=review.service.owner,
            notification_type='review',
            title_ar='تقييم جديد',
            title_en='New Review',
            message_ar=f'قام {self.request.user.full_name} بتقييم خدمتك "{review.service.title_ar}" بـ {review.rating} نجوم.',
            message_en=f'{self.request.user.full_name} reviewed your service "{review.service.title_en}" with {review.rating} stars.',
            related_object=review
        )

    @action(detail=True, methods=['post'])
    def mark_helpful(self, request, pk=None):
        """
        Mark a review as helpful or not helpful.
        """
        review = self.get_object()
        vote = request.data.get('vote')  # 'helpful' or 'unhelpful'
        
        if vote not in ['helpful', 'unhelpful']:
            return Response(
                {'error': 'Invalid vote. Must be "helpful" or "unhelpful"'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Check if user already voted
        existing_vote = ReviewHelpfulness.objects.filter(
            review=review,
            voter=request.user
        ).first()
        
        if existing_vote:
            if existing_vote.vote == vote:
                return Response(
                    {'error': 'You have already voted this way'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            else:
                # Update existing vote
                existing_vote.vote = vote
                existing_vote.save()
        else:
            # Create new vote
            ReviewHelpfulness.objects.create(
                review=review,
                voter=request.user,
                vote=vote
            )
        
        # Update review helpfulness counts
        review.helpful_count = review.helpfulness_votes.filter(vote='helpful').count()
        review.unhelpful_count = review.helpfulness_votes.filter(vote='unhelpful').count()
        review.save()
        
        return Response({
            'helpful_count': review.helpful_count,
            'unhelpful_count': review.unhelpful_count
        })

    @action(detail=False, methods=['get'])
    def my_reviews(self, request):
        """
        Get current user's reviews.
        """
        reviews = Review.objects.filter(reviewer=request.user, is_active=True)
        serializer = self.get_serializer(reviews, many=True)
        return Response(serializer.data)