from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.utils import timezone
from django.db import models
from .models import CustomUser, FoodItem, Meal, MealFoodItem, DailyProgress, WeightLog, ProgressPhoto, WaterIntake, WaterGoal
from .forms import CustomUserCreationForm, CustomAuthenticationForm, UserProfileForm, FoodSearchForm, MealForm, FoodItemForm, WeightLogForm, ProgressPhotoForm, WaterIntakeForm, WaterGoalForm
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
        
        # Add food items to meal and calculate totals
        total_calories = 0
        total_protein = 0
        total_carbs = 0
        total_fat = 0
        
        for item in food_items:
            food_item = FoodItem.objects.get(id=item['food_id'])
            quantity = item.get('quantity', 1)
            MealFoodItem.objects.create(
                meal=meal,
                food_item=food_item,
                quantity=quantity
            )
            total_calories += food_item.calories * quantity
            total_protein += food_item.protein * quantity
            total_carbs += food_item.carbs * quantity
            total_fat += food_item.fat * quantity
        
        # Update daily progress with macros
        today = timezone.now().date()
        daily_progress, created = DailyProgress.objects.get_or_create(
            user=request.user,
            date=today,
            defaults={
                'total_calories_consumed': total_calories,
                'total_protein': total_protein,
                'total_carbs': total_carbs,
                'total_fat': total_fat
            }
        )
        
        if not created:
            daily_progress.total_calories_consumed += total_calories
            daily_progress.total_protein += total_protein
            daily_progress.total_carbs += total_carbs
            daily_progress.total_fat += total_fat
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

# Phase 1: Weight Tracking
@login_required
def weight_log(request):
    weight_logs = WeightLog.objects.filter(user=request.user).order_by('-date')[:30]  # Last 30 entries
    
    if request.method == 'POST':
        form = WeightLogForm(request.POST)
        if form.is_valid():
            weight_log = form.save(commit=False)
            weight_log.user = request.user
            
            # Check if entry already exists for this date
            existing_log = WeightLog.objects.filter(user=request.user, date=weight_log.date).first()
            if existing_log:
                existing_log.weight = weight_log.weight
                existing_log.notes = weight_log.notes
                existing_log.save()
                messages.success(request, f'Weight updated for {weight_log.date}')
            else:
                weight_log.save()
                messages.success(request, f'Weight logged for {weight_log.date}')
            
            return redirect('weight_log')
    else:
        form = WeightLogForm(initial={'date': timezone.now().date()})
    
    # Prepare data for chart
    weight_data = list(WeightLog.objects.filter(user=request.user)
                                  .order_by('date')
                                  .values('date', 'weight')[:30])
    
    context = {
        'form': form,
        'weight_logs': weight_logs,
        'weight_data': weight_data,
        'current_weight': weight_logs.first().weight if weight_logs else None,
    }
    return render(request, 'weight_log.html', context)

# Phase 1: Progress Photos
@login_required
def progress_photos(request):
    photos = ProgressPhoto.objects.filter(user=request.user).order_by('-date')
    
    if request.method == 'POST':
        form = ProgressPhotoForm(request.POST, request.FILES)
        if form.is_valid():
            photo = form.save(commit=False)
            photo.user = request.user
            photo.save()
            messages.success(request, 'Progress photo added successfully!')
            return redirect('progress_photos')
    else:
        form = ProgressPhotoForm(initial={'date': timezone.now().date()})
    
    context = {
        'form': form,
        'photos': photos,
    }
    return render(request, 'progress_photos.html', context)

@login_required
def delete_progress_photo(request, photo_id):
    photo = get_object_or_404(ProgressPhoto, id=photo_id, user=request.user)
    if request.method == 'POST':
        photo.delete()
        messages.success(request, 'Progress photo deleted successfully!')
        return redirect('progress_photos')
    return redirect('progress_photos')

# Phase 1: Water Tracking
@login_required
def water_tracker(request):
    today = timezone.now().date()
    water_intakes = WaterIntake.objects.filter(user=request.user, date=today).order_by('-time')
    
    # Get or create water goal
    water_goal, created = WaterGoal.objects.get_or_create(
        user=request.user,
        defaults={'daily_goal_ml': 2000}
    )
    
    # Calculate today's total
    total_water_today = water_intakes.aggregate(total=models.Sum('amount_ml'))['total'] or 0
    water_percentage = min(100, (total_water_today / water_goal.daily_goal_ml) * 100) if water_goal.daily_goal_ml > 0 else 0
    
    if request.method == 'POST':
        if 'add_water' in request.POST:
            water_form = WaterIntakeForm(request.POST)
            if water_form.is_valid():
                water_intake = water_form.save(commit=False)
                water_intake.user = request.user
                water_intake.date = today
                water_intake.save()
                messages.success(request, f'Added {water_intake.amount_ml}ml water intake!')
                return redirect('water_tracker')
        
        elif 'set_goal' in request.POST:
            goal_form = WaterGoalForm(request.POST, instance=water_goal)
            if goal_form.is_valid():
                goal_form.save()
                messages.success(request, f'Water goal updated to {water_goal.daily_goal_ml}ml!')
                return redirect('water_tracker')
    else:
        water_form = WaterIntakeForm()
        goal_form = WaterGoalForm(instance=water_goal)
    
    context = {
        'water_form': water_form,
        'goal_form': goal_form,
        'water_intakes': water_intakes,
        'total_water_today': total_water_today,
        'water_goal': water_goal,
        'water_percentage': water_percentage,
    }
    return render(request, 'water_tracker.html', context)

@login_required
def delete_water_intake(request, intake_id):
    water_intake = get_object_or_404(WaterIntake, id=intake_id, user=request.user)
    if request.method == 'POST':
        water_intake.delete()
        messages.success(request, 'Water intake deleted successfully!')
        return redirect('water_tracker')
    return redirect('water_tracker')

# Phase 1: Quick Add Food
@login_required
def quick_add_food(request, food_id):
    """Quick add a common food to today's meals"""
    food_item = get_object_or_404(FoodItem, id=food_id)
    
    if request.method == 'POST':
        # Create a quick snack meal
        meal = Meal.objects.create(user=request.user, meal_type='SNACK')
        MealFoodItem.objects.create(meal=meal, food_item=food_item, quantity=1)
        
        # Update daily progress
        today = timezone.now().date()
        daily_progress, created = DailyProgress.objects.get_or_create(
            user=request.user,
            date=today,
            defaults={
                'total_calories_consumed': food_item.calories,
                'total_protein': food_item.protein,
                'total_carbs': food_item.carbs,
                'total_fat': food_item.fat
            }
        )
        
        if not created:
            daily_progress.total_calories_consumed += food_item.calories
            daily_progress.total_protein += food_item.protein
            daily_progress.total_carbs += food_item.carbs
            daily_progress.total_fat += food_item.fat
            daily_progress.save()
        
        messages.success(request, f'Added {food_item.name} to your daily log!')
        return redirect('dashboard')
    
    return redirect('dashboard')

@login_required
def get_quick_add_foods(request):
    """Get commonly logged foods for quick add"""
    # Get user's most frequently logged foods
    common_foods = FoodItem.objects.filter(
        mealfooditem__meal__user=request.user
    ).annotate(
        log_count=models.Count('mealfooditem')
    ).order_by('-log_count')[:6]
    
    # If not enough, get system common foods
    if len(common_foods) < 6:
        system_foods = FoodItem.objects.filter(created_by__isnull=True).exclude(
            id__in=[f.id for f in common_foods]
        )[:6-len(common_foods)]
        common_foods = list(common_foods) + list(system_foods)
    
    food_data = [{
        'id': food.id,
        'name': food.name,
        'calories': food.calories,
        'protein': food.protein,
        'carbs': food.carbs,
        'fat': food.fat,
        'serving_size': food.serving_size
    } for food in common_foods]
    
    return JsonResponse(food_data, safe=False)

    