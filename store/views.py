from datetime import datetime
import uuid
from django.shortcuts import render
from rest_framework import viewsets, status, generics, permissions
from rest_framework.response import Response
from rest_framework.decorators import action
from .models import Product, Cart, CartItem, Order
from .serializers import ProductSerializer, CartSerializer, CartItemSerializer, OrderSerializer, UserSerializer
from rave_python import Rave, RaveExceptions
from rest_framework.views import APIView
from .models import User

class ProductViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer

class CartViewSet(viewsets.ModelViewSet):
    queryset = Cart.objects.all()
    serializer_class = CartSerializer

    @action(detail=True, methods=['post'])
    def add_item(self, request, pk=None):
        cart = self.get_object()
        product_id = request.data.get('product_id')
        quantity = request.data.get('quantity', 1)
        product = Product.objects.get(id=product_id)
        cart_item, created = CartItem.objects.get_or_create(cart=cart, product=product)
        cart_item.quantity += int(quantity)
        cart_item.save()
        return Response({'status': 'item added'})

    @action(detail=True, methods=['post'])
    def checkout(self, request, pk=None):
        cart = self.get_object()
        total_price = sum(item.product.price * item.quantity for item in cart.items.all())
        order = Order.objects.create(user_id=cart.user_id, total_price=total_price)
        cart.items.all().delete()
        return Response({'status': 'order created', 'order_id': order.id})

class OrderViewSet(viewsets.ModelViewSet):
    queryset = Order.objects.all()
    serializer_class = OrderSerializer

class FlutterwavePaymentView(APIView):

    def generateTransactionReference(self):
        """
        Funtion to generate a unique transaction reference.
        Combines timestamp and a UUID.
        """
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        unique_id = str(uuid.uuid4()).replace("-", "")

        transaction_ref = f"TX-{timestamp}-{unique_id[:8]}"
    
        return transaction_ref

    def post(self, request, *args, **kwargs):
        data = request.data
        print("Received data:", data)  # For Debug delete later
        txRef = self.generateTransactionReference()
        payload = {
            "cardno": data.get("cardno"),
            "cvv": data.get("cvv"),
            "expirymonth": data.get("expirymonth"),
            "expiryyear": data.get("expiryyear"),
            "amount": data.get("amount"),
            "email": data.get("email"),
            "currency": data.get("currency"),
            "redirect_url": data.get("redirect_url"),
            "customer": data.get("customer"),
            "customizations": data.get("customizations"),
            "txRef": txRef,
            "tx_ref": data.get("txRef")
        }
        print("Payload:", payload)  # For Debug
        try:
            rave = Rave("settings.FLUTTERWAVE_SECRET_KEY", "settings.FLUTTERWAVE_PUBLIC_KEY", usingEnv=False)
            response = rave.Card.charge(payload)
            print("Flutterwave Response:", response)  # Debugging
            if response.get("status") == "success":
                return Response({"message": "Payment successful", "data": response}, status=status.HTTP_200_OK)
            else:
                return Response({"error": "Payment failed", "data": response}, status=status.HTTP_400_BAD_REQUEST)
        except RaveExceptions.CardChargeError as e:
            print("Flutterwave Error:", str(e))
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        


# Create your views here.
class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [permissions.AllowAny]

    def perform_create(self, serializer):
        user = serializer.save()
        cart = Cart.objects.create(user=user)
        self.cart_id = cart.id

    def create(self, request, *args, **kwargs):
        response = super().create(request, *args, **kwargs)
        response.data = {
            'status': 'user and cart created',
            'user_id': response.data['id'],
            'cart_id': self.cart_id 
        }
        return response