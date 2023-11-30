from django.shortcuts import get_object_or_404
from django.contrib.auth.models import User, Group
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import status
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet
from rest_framework.decorators import api_view, permission_classes, throttle_classes
from rest_framework.filters import SearchFilter, OrderingFilter
from rest_framework.permissions import (
    IsAdminUser,
    IsAuthenticated,
    DjangoModelPermissions,
    DjangoModelPermissionsOrAnonReadOnly,
)
from rest_framework.throttling import UserRateThrottle, AnonRateThrottle
from .paginations import MenuItemPagination
from .serializers import *
from .filters import *
from .permissions import *


# Create your views here.
class CategoryViewSet(ModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [IsAdminUser, DjangoModelPermissions]
    throttle_classes = [UserRateThrottle, AnonRateThrottle]


class MenuItemViewSet(ModelViewSet):
    queryset = MenuItem.objects.select_related("category").all()
    serializer_class = MenuItemSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_class = MenuItemFilter
    search_fields = ["title", "category__title"]
    ordering_fields = ["price", "featured", "category"]
    pagination_class = MenuItemPagination
    permission_classes = [DjangoModelPermissionsOrAnonReadOnly]
    throttle_classes = [UserRateThrottle, AnonRateThrottle]


# class CartItemViewSet(ModelViewSet):
#     serializer_class = CartItemSerializer
#     permission_classes = [DjangoModelPermissions]
#     queryset = CartItem.objects.all()

# def get_queryset(self):
#     user = self.request.user

#     cart = Cart.objects.get(user=user)
#     if cart:
#         return CartItem.objects.filter(cart_id=cart["pk"]).select_related(
#             "menuitem"
#         )
#     return "User has no cart"


class CartViewSet(ModelViewSet):
    http_method_names = ["get", "post", "patch", "delete", "head", "options"]
    throttle_classes = [UserRateThrottle, AnonRateThrottle]
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        if self.request.method == "POST":
            return AddCartSerializer
        elif self.request.method == "PATCH":
            return UpdateCartSerializer
        return CartSerializer

    def get_serializer_context(self):
        return {"user_id": self.request.user.id}

    def get_queryset(self):
        user = self.request.user.id
        try:
            return Cart.objects.filter(user_id=user).select_related("menuitem").all()
        except Cart.DoesNotExist:
            return Cart.objects.create(user_id=user)

    # @action(
    #     detail=True,
    #     methods=["GET", "POST", "PATCH", "DELETE"],
    #     permission_classes=[IsAuthenticated],
    # )
    # def items(self, request):
    #     user_id = request.user.id
    #     cart = Cart.objects.only("id").get(user=user_id)
    #     items = CartItem.objects.get(id=cart.id)
    #     serializer = CartItemSerializer(items)
    #     return Response(serializer.data)


# class OrderItemViewSet(ModelViewSet):
#     queryset = OrderItem.objects.select_related("menuitem").all()
#     serializer_class = OrderItemSerializer


class OrderViewSet(ModelViewSet):
    http_method_names = ["get", "post", "patch", "delete", "head", "options"]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_class = OrderFilter
    search_fields = ["user__first_name", "orderitem__menuitem__title"]
    ordering_fields = ["total", "status", "date"]
    throttle_classes = [UserRateThrottle, AnonRateThrottle]

    def get_permissions(self):
        if self.request.method in ["PATCH", "DELETE"]:
            return [DjangoModelPermissions()]
        return [IsAuthenticated()]

    def get_queryset(self):
        user = self.request.user
        if user.is_staff:
            return Order.objects.all()
        if user.groups.filter(name="Delivery Crew").exists():
            return (
                Order.objects.filter(delivery_crew_id=user.id)
                .select_related("user")
                .all()
            )
        return Order.objects.filter(user_id=user.id).select_related("user").all()

    def get_serializer_class(self):
        user = self.request.user
        if self.request.method == "POST":
            return CreateOrderSerializer
        elif self.request.method == "PATCH":
            return UpdateOrderSerializer
        else:
            if user.is_staff:
                return OrderSerializer
            return SimpleOrderSerializer

    def create(self, request, *args, **kwargs):
        serializer = CreateOrderSerializer(
            data=request.data, context={"user_id": self.request.user.id}  # type: ignore
        )
        serializer.is_valid(raise_exception=True)
        order = (
            serializer.save()
        )  # order is the order we returned from the CreateOrderSerializer save func
        serializer = SimpleOrderSerializer(order)
        return Response(serializer.data)


@api_view(["GET", "POST", "DELETE"])
@permission_classes([IsAdminUser])
@throttle_classes([UserRateThrottle, AnonRateThrottle])
def manager(request):
    managers = Group.objects.get(name="Manager")
    if request.method == "GET":
        users = [user.username for user in User.objects.filter(groups=managers).all()]
        return Response({"Managers": users})

    username = request.data["username"]
    if username:
        user = get_object_or_404(User, username=username)
        if request.method == "POST":
            managers.user_set.add(user)
            user.is_staff = True
            user.save()
            return Response(
                {"message": "User assigned to Manager group"}, status.HTTP_201_CREATED
            )
        elif request.method == "DELETE":
            managers.user_set.remove(user)
            user.is_staff = False
            user.save()
            return Response(
                {"message": "User removed from Manager group"}, status.HTTP_200_OK
            )

    return Response({"message": "error"}, status.HTTP_400_BAD_REQUEST)


@api_view(["GET", "POST", "DELETE"])
@permission_classes([IsAdminUser])
@throttle_classes([UserRateThrottle, AnonRateThrottle])
def delivery_crew(request):
    delivery_crew = Group.objects.get(name="Delivery Crew")
    if request.method == "GET":
        users = [
            user.username for user in User.objects.filter(groups=delivery_crew).all()
        ]
        return Response({"Delivery Crew": users})

    username = request.data["username"]
    if username:
        user = get_object_or_404(User, username=username)
        if request.method == "POST":
            delivery_crew.user_set.add(user)
            return Response(
                {"message": "User assigned to Delivery Crew"}, status.HTTP_201_CREATED
            )
        elif request.method == "DELETE":
            delivery_crew.user_set.remove(user)
            return Response(
                {"message": "User removed from Delivery Crew"}, status.HTTP_200_OK
            )

    return Response({"message": "error"}, status.HTTP_400_BAD_REQUEST)
