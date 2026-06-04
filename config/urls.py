from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/auth/', include('users.urls')),
    path('api/ouvriers/', include('ouvriers.urls')),
    path('api/pointages/', include('pointages.urls')),
    path('api/paiements/', include('paiements.urls')),
    path('api/rapports/', include('rapports.urls')),
]