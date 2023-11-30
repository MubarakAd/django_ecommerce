"""
URL configuration for api project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from drf_yasg.views import get_schema_view
from drf_yasg import openapi
from rest_framework import permissions
from rest_framework_nested import routers
from shop import views
from cart.views import CartItemViewSet, CartViewSet
from order import views as order_view
from django.conf import settings
from django.conf.urls.static import static

router = routers.DefaultRouter()
router.register('products', views.ProductViewSet, basename='product')
router.register('categories', views.CategoryViewSet, basename='category')
# router.register('users', UserViewSet)
router.register('carts', CartViewSet, basename='cart')

# Create a nested router for cart items
cart_router = routers.NestedDefaultRouter(router, 'carts', lookup='cart')
cart_router.register('items', CartItemViewSet, basename='cart-items')

# Create a router for orders
router.register('order', order_view.OrderViewSet, basename='order')

# Create a nested router for order items
order_router = routers.NestedDefaultRouter(router, 'order', lookup='order')
order_router.register('items', order_view.OrderItemViewSet, basename='order-items')


schema_view = get_schema_view(
   openapi.Info(
      title="Ecommerce API",
      default_version='v1',
      description="Test description",
      terms_of_service="http://localhos:8000/policies/terms/",
      contact=openapi.Contact(email="contact@api.local"),
      license=openapi.License(name="API License"),
   ),
   public=True,
   permission_classes=(permissions.AllowAny,),
)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('__debug__/', include('debug_toolbar.urls')),
    path('auth/', include('authentication.urls')),
    # path('cart/', include('cart.urls')),
    # path('order/', include('order.urls')),
    # path('shop/', include('shop.urls')),
    path('', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
] + router.urls + cart_router.urls + order_router.urls
urlpatterns +=  static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)