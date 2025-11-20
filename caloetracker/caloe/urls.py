from django.urls import path
from . import views

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('profile/', views.profile_view, name='profile'),
    path('food-search/', views.food_search, name='food_search'),
    path('add-meal/', views.add_meal, name='add_meal'),
    path('delete-meal/<int:meal_id>/', views.delete_meal, name='delete_meal'),
    path('daily-progress/', views.get_daily_progress, name='daily_progress'),
    path('add-food-item/', views.add_food_item, name='add_food_item'),
    path('my-food-items/', views.my_food_items, name='my_food_items'),
    path('delete-food-item/<int:food_id>/', views.delete_food_item, name='delete_food_item'),
    path('weight-log/', views.weight_log, name='weight_log'),
    path('progress-photos/', views.progress_photos, name='progress_photos'),
    path('delete-photo/<int:photo_id>/', views.delete_progress_photo, name='delete_progress_photo'),
    path('water-tracker/', views.water_tracker, name='water_tracker'),
    path('delete-water/<int:intake_id>/', views.delete_water_intake, name='delete_water_intake'),
    path('quick-add/<int:food_id>/', views.quick_add_food, name='quick_add_food'),
    path('quick-add-foods/', views.get_quick_add_foods, name='get_quick_add_foods'),
]