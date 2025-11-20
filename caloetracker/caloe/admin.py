from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser, FoodItem, Meal, MealFoodItem, DailyProgress, WeightLog, ProgressPhoto, WaterIntake, WaterGoal

@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    list_display = ('username', 'email', 'age', 'gender', 'height', 'weight', 'goal')
    list_filter = ('gender', 'goal')
    fieldsets = UserAdmin.fieldsets + (
        ('Personal Info', {'fields': ('age', 'gender', 'height', 'weight', 'goal', 'activity_level', 'protein_goal', 'carbs_goal', 'fat_goal')}),
    )

@admin.register(FoodItem)
class FoodItemAdmin(admin.ModelAdmin):
    list_display = ('name', 'calories', 'protein', 'carbs', 'fat', 'serving_size', 'is_custom', 'created_by')
    search_fields = ('name',)
    list_filter = ('is_custom',)

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

# Phase 1: Register new models
@admin.register(WeightLog)
class WeightLogAdmin(admin.ModelAdmin):
    list_display = ('user', 'date', 'weight', 'created_at')
    list_filter = ('date',)
    search_fields = ('user__username',)

@admin.register(ProgressPhoto)
class ProgressPhotoAdmin(admin.ModelAdmin):
    list_display = ('user', 'date', 'caption', 'created_at')
    list_filter = ('date',)

@admin.register(WaterIntake)
class WaterIntakeAdmin(admin.ModelAdmin):
    list_display = ('user', 'date', 'amount_ml', 'time')
    list_filter = ('date',)

@admin.register(WaterGoal)
class WaterGoalAdmin(admin.ModelAdmin):
    list_display = ('user', 'daily_goal_ml')