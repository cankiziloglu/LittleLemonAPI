from django.contrib import admin
from .models import *


# Register your models here.
@admin.register(MenuItem)
class MenuItemAdmin(admin.ModelAdmin):
    list_display = ["title", "price", "featured", "category_title"]
    list_editable = ["price"]
    list_select_related = ["category"]

    def category_title(self, menuitem: MenuItem):
        return menuitem.category.title


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ["title"]


admin.site.register(Cart)
admin.site.register(Order)
admin.site.register(OrderItem)
