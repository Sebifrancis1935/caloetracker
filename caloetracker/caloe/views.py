from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.utils import timezone
from django.db import models
from .models import CustomUser, FoodItem, Meal, MealFoodItem, DailyProgress
from .forms import CustomUserCreationForm, CustomAuthenticationForm, UserProfileForm, FoodSearchForm, MealForm, FoodItemForm  # ADD FoodItemForm HERE
import json

def register_view(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, 'Registration successful!')
            return redirect('dashboard')
    else:
        form = CustomUserCreationForm()
    return render(request, 'registration/register.html', {'form': form})

def login_view(request):
    if request.method == 'POST':
        form = CustomAuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                messages.success(request, f'Welcome back, {username}!')
                return redirect('dashboard')
    else:
        form = CustomAuthenticationForm()
    return render(request, 'registration/login.html', {'form': form})

def logout_view(request):
    logout(request)
    messages.info(request, 'You have been logged out.')
    return redirect('login')

@login_required
def dashboard(request):
    today = timezone.now().date()
    
    # Get or create daily progress
    daily_progress, created = DailyProgress.objects.get_or_create(
        user=request.user,
        date=today,
        defaults={'total_calories_consumed': 0}
    )
    
    # Get today's meals
    today_meals = Meal.objects.filter(user=request.user, date=today).order_by('-created_at')
    
    context = {
        'user': request.user,
        'daily_progress': daily_progress,
        'today_meals': today_meals,
        'maintenance_calories': request.user.calculate_maintenance_calories(),
        'daily_target': request.user.get_daily_calorie_target(),
    }
    return render(request, 'dashboard.html', context)

@login_required
def profile_view(request):
    if request.method == 'POST':
        form = UserProfileForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Profile updated successfully!')
            return redirect('profile')
    else:
        form = UserProfileForm(instance=request.user)
    
    context = {
        'form': form,
        'maintenance_calories': request.user.calculate_maintenance_calories(),
        'daily_target': request.user.get_daily_calorie_target(),
    }
    return render(request, 'profile.html', context)

@login_required
def food_search(request):
    # Show both system foods and user's custom foods
    food_items = FoodItem.objects.filter(
        models.Q(created_by__isnull=True) |  # System foods
        models.Q(created_by=request.user)    # User's custom foods
    )
    
    form = FoodSearchForm(request.GET or None)
    
    if form.is_valid() and form.cleaned_data['search_query']:
        query = form.cleaned_data['search_query']
        food_items = food_items.filter(name__icontains=query)
    
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        food_data = [{
            'id': food.id,
            'name': food.name,
            'calories': food.calories,
            'protein': food.protein,
            'carbs': food.carbs,
            'fat': food.fat,
            'serving_size': food.serving_size,
            'is_custom': food.is_custom
        } for food in food_items]
        return JsonResponse(food_data, safe=False)
    
    return render(request, 'food_search.html', {'form': form, 'food_items': food_items})

@login_required
def add_meal(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        meal_type = data.get('meal_type')
        food_items = data.get('food_items', [])
        
        # Create meal
        meal = Meal.objects.create(user=request.user, meal_type=meal_type)
        
        # Add food items to meal
        total_calories = 0
        for item in food_items:
            food_item = FoodItem.objects.get(id=item['food_id'])
            quantity = item.get('quantity', 1)
            MealFoodItem.objects.create(
                meal=meal,
                food_item=food_item,
                quantity=quantity
            )
            total_calories += food_item.calories * quantity
        
        # Update daily progress
        today = timezone.now().date()
        daily_progress, created = DailyProgress.objects.get_or_create(
            user=request.user,
            date=today,
            defaults={'total_calories_consumed': total_calories}
        )
        
        if not created:
            daily_progress.total_calories_consumed += total_calories
            daily_progress.save()
        
        return JsonResponse({'success': True, 'meal_id': meal.id})
    
    form = MealForm()
    return render(request, 'add_meal.html', {'form': form})

@login_required
def get_daily_progress(request):
    today = timezone.now().date()
    daily_progress, created = DailyProgress.objects.get_or_create(
        user=request.user,
        date=today,
        defaults={'total_calories_consumed': 0}
    )
    
    data = {
        'total_consumed': daily_progress.total_calories_consumed,
        'calories_remaining': daily_progress.calories_remaining(),
        'daily_target': request.user.get_daily_calorie_target(),
        'progress_percentage': daily_progress.progress_percentage(),
    }
    
    return JsonResponse(data)

@login_required
def delete_meal(request, meal_id):
    if request.method == 'DELETE':
        meal = get_object_or_404(Meal, id=meal_id, user=request.user)
        
        # Calculate total calories to subtract
        total_calories = sum(item.total_calories for item in meal.food_items.all())
        
        # Update daily progress
        today = timezone.now().date()
        daily_progress = get_object_or_404(DailyProgress, user=request.user, date=today)
        daily_progress.total_calories_consumed = max(0, daily_progress.total_calories_consumed - total_calories)
        daily_progress.save()
        
        # Delete meal
        meal.delete()
        
        return JsonResponse({'success': True})

# ADD THESE NEW VIEWS FOR FOOD ITEM MANAGEMENT
@login_required
def add_food_item(request):
    if request.method == 'POST':
        form = FoodItemForm(request.POST)
        if form.is_valid():
            food_item = form.save(commit=False)
            food_item.created_by = request.user
            food_item.is_custom = True
            food_item.save()
            messages.success(request, f'"{food_item.name}" has been added to your food database!')
            return redirect('food_search')
    else:
        form = FoodItemForm()
    
    return render(request, 'add_food_item.html', {'form': form})

@login_required
def my_food_items(request):
    # Show only custom food items created by the user
    custom_foods = FoodItem.objects.filter(created_by=request.user, is_custom=True)
    return render(request, 'my_food_items.html', {'custom_foods': custom_foods})

@login_required
def delete_food_item(request, food_id):
    food_item = get_object_or_404(FoodItem, id=food_id, created_by=request.user)
    if request.method == 'POST':
        food_name = food_item.name
        food_item.delete()
        messages.success(request, f'"{food_name}" has been deleted from your food database.')
        return redirect('my_food_items')
    return redirect('my_food_items')