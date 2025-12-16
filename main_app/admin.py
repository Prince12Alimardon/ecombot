from django.contrib import admin
from .models import Product, Order, OrderItem
# Register your models here.


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'price', )
    list_filter = ('name', 'price', )
    search_fields = ('name', 'price', )


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('full_name', 'total_price', 'phone',)
    list_filter = ('full_name', 'total_price', 'phone',)
    search_fields = ('full_name', 'total_price', 'phone',)


@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ('product', 'quantity', 'price',)
    list_filter = ('product', 'quantity', 'price',)
    search_fields = ('product', 'quantity', 'price',)
