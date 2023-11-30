from rest_framework.pagination import PageNumberPagination


class MenuItemPagination(PageNumberPagination):
    page_query_param = "page"
    page_size_query_param = "perpage"
    max_page_size = 20
    page_size = 5
