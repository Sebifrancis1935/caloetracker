from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser, FoodItem, Meal, MealFoodItem, DailyProgress

@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    list_display = ('username', 'email', 'age', 'gender', 'height', 'weight', 'goal')
    list_filter = ('gender', 'goal')
    fieldsets = UserAdmin.fieldsets + (
        ('Personal Info', {'fields': ('age', 'gender', 'height', 'weight', 'goal', 'activity_level')}),
    )

@admin.register(FoodItem)
class FoodItemAdmin(admin.ModelAdmin):
    list_display = ('name', 'calories', 'protein', 'carbs', 'fat', 'serving_size')
    search_fields = ('name',)

@admin.register(Meal)
class MealAdmin(admin.ModelAdmin):
    list_display = ('user', 'meal_type', 'date', 'created_at')
    list_filter = ('meal_type', 'date')

@admin.register(MealFoodItem)
class MealFoodItemAdmin(admin.ModelAdmin):
    list_display = ('meal', 'food_item', 'quantity', 'total_calories')

@admin.register(DailyProgress)
class DailyProgressAdmin(admin.ModelAdmin):
    list_display = ('user', 'date', 'total_calories_consumed', 'calories_remaining')
    list_filter = ('date',)