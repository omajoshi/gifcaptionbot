from django.urls import include, path

from . import views


app_name='trimgif'

urlpatterns = [
    path('create/', views.create, name='create'),
    path('', views.search, name='search'),
]
