from django.urls import path, include
from rest_framework import routers
from .views import *

router = routers.DefaultRouter()
router.register("categories", CategoryViewSet)
router.register("menu-items", MenuItemViewSet)
router.register("cart", CartViewSet, basename="cart")
router.register("orders", OrderViewSet, basename="orders")

urlpatterns = [
    path("", include(router.urls)),
    path("groups/manager/users", manager),
    path("groups/delivery-crew/users", delivery_crew),
]
