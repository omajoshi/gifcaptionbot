from django.urls import include, path

from . import views


app_name='trimgif'

urlpatterns = [
    path('see/<slug:task_id>/', views.check_result, name='submits'),
    path('submit/', views.submit, name='submit'),
    path('edit/', views.edit, name='edit'),
    path('', views.search, name='search'),
]
