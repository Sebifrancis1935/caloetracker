from django.core.management.base import BaseCommand
from caloe.models import CustomUser, FoodItem, Meal, MealFoodItem, DailyProgress, WeightLog, WaterIntake, WaterGoal
from django.utils import timezone
from datetime import timedelta
import random

class Command(BaseCommand):
    help = 'Create simple sample data'

    def add_arguments(self, parser):
        parser.add_argument('username', type=str)

    def handle(self, *args, **options):
        username = options['username']
        
        try:
            user = CustomUser.objects.get(username=username)
        except CustomUser.DoesNotExist:
            print(f'❌ User {username} does not exist')
            return

        print(f'🚀 Creating simple data for: {username}')

        # Get food items
        foods = list(FoodItem.objects.all())
        if not foods:
            print('❌ No food items found. Run populate_food_items first.')
            return

        # Set water goal
        WaterGoal.objects.get_or_create(user=user, defaults={'daily_goal_ml': 2500})

        # Create data for last 7 days
        today = timezone.now().date()
        
        for day in range(7):
            date = today - timedelta(days=6-day)
            print(f'Creating data for {date}')
            
            # Weight data
            WeightLog.objects.create(
                user=user,
                date=date,
                weight=75.0 - (day * 0.1),
                notes=f'Day {day+1}'
            )
            
            # Water data (2 entries per day)
            WaterIntake.objects.create(user=user, date=date, amount_ml=300)
            WaterIntake.objects.create(user=user, date=date, amount_ml=400)
            
            # One meal per day
            meal = Meal.objects.create(user=user, meal_type='LUNCH', date=date)
            for food in random.sample(foods, 2):
                MealFoodItem.objects.create(
                    meal=meal,
                    food_item=food,
                    quantity=1.0
                )
            
            # Daily progress
            DailyProgress.objects.create(
                user=user,
                date=date,
                total_calories_consumed=1800 + (day * 50),
                total_protein=70,
                total_carbs=200,
                total_fat=50
            )
        
        print('✅ SIMPLE DATA CREATION COMPLETE!')
        print('📊 You now have 7 days of data for analytics!')