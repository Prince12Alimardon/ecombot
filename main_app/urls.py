from django.urls import path
from .views import ProductListAPIView, CreateOrderView

urlpatterns = [
    path("products/", ProductListAPIView.as_view()),
    path("orders/", CreateOrderView.as_view()),
]
