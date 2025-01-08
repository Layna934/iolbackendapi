from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import FlutterwavePaymentView, ProductViewSet, CartViewSet, OrderViewSet, RegisterView
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView, TokenVerifyView

router = DefaultRouter()
router.register(r'products', ProductViewSet)
router.register(r'carts', CartViewSet)
router.register(r'orders', OrderViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path('pay/', FlutterwavePaymentView.as_view(), name='flutterwave_payment'),
    path('auth/register/', RegisterView.as_view(), name='register'),
    path('auth/login/', TokenObtainPairView.as_view(), name='login'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
]