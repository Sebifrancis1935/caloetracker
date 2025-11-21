from django.core.management.base import BaseCommand
from caloe.models import CustomUser, FoodItem, Meal, MealFoodItem, DailyProgress, WeightLog, WaterIntake, WaterGoal
from django.utils import timezone
from datetime import timedelta
import random

class Command(BaseCommand):
    help = 'Bulletproof data creation - checks for existing data before creating'

    def add_arguments(self, parser):
        parser.add_argument('username', type=str)

    def handle(self, *args, **options):
        username = options['username']
        
        try:
            user = CustomUser.objects.get(username=username)
        except CustomUser.DoesNotExist:
            self.stdout.write(self.style.ERROR(f'User {username} does not exist'))
            return

        self.stdout.write(self.style.SUCCESS(f'🚀 Creating bulletproof data for: {username}'))

        # Get food items
        foods = list(FoodItem.objects.all())
        if not foods:
            self.stdout.write(self.style.ERROR('❌ No food items found. Run populate_food_items first.'))
            return

        # Set water goal
        WaterGoal.objects.get_or_create(user=user, defaults={'daily_goal_ml': 2500})

        # Create data for last 14 days (smaller set for testing)
        today = timezone.now().date()
        days_to_create = 14
        
        successful_days = 0
        
        for day in range(days_to_create):
            date = today - timedelta(days=days_to_create-1-day)
            
            try:
                self.stdout.write(f'📅 Creating data for {date}...')
                
                # Check if data already exists for this date
                if self.data_exists_for_date(user, date):
                    self.stdout.write(self.style.WARNING(f'   ⚠️  Data already exists for {date}, skipping...'))
                    continue
                
                # Create weight data
                self.create_weight_for_day(user, date, day)
                
                # Create water data
                self.create_water_for_day(user, date)
                
                # Create meals and progress
                self.create_meals_and_progress(user, date, foods)
                
                successful_days += 1
                self.stdout.write(self.style.SUCCESS(f'   ✅ Created data for {date}'))
                
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'   ❌ Error for {date}: {str(e)}'))
                continue
        
        self.stdout.write(self.style.SUCCESS(f'\n🎉 SUCCESS! Created data for {successful_days} out of {days_to_create} days'))
        self.stdout.write(self.style.SUCCESS('📊 You can now view graphs and analytics!'))

    def data_exists_for_date(self, user, date):
        """Check if any data already exists for this date"""
        return (DailyProgress.objects.filter(user=user, date=date).exists() or
                WeightLog.objects.filter(user=user, date=date).exists() or
                WaterIntake.objects.filter(user=user, date=date).exists() or
                Meal.objects.filter(user=user, date=date).exists())

    def create_weight_for_day(self, user, date, day):
        """Create weight data for a specific day"""
        base_weight = user.weight or 75.0
        
        # Create realistic trend based on goal
        if user.goal == 'LOSE':
            trend = -0.1
            weight = base_weight - (day * trend) + random.uniform(-0.3, 0.3)
        elif user.goal == 'GAIN':
            trend = 0.08
            weight = base_weight + (day * trend) + random.uniform(-0.3, 0.3)
        else:  # MAINTAIN
            weight = base_weight + random.uniform(-0.5, 0.5)
        
        # Use get_or_create to be safe
        WeightLog.objects.get_or_create(
            user=user,
            date=date,
            defaults={
                'weight': round(weight, 1),
                'notes': f'Day {day+1} progress'
            }
        )

    def create_water_for_day(self, user, date):
        """Create water intake for a specific day"""
        # Create 2-4 water entries per day
        for i in range(random.randint(2, 4)):
            amount = random.choice([250, 300, 400, 500])
            WaterIntake.objects.create(
                user=user,
                date=date,
                amount_ml=amount
            )

    def create_meals_and_progress(self, user, date, foods):
        """Create meals and daily progress for a specific day"""
        total_calories = 0
        total_protein = 0
        total_carbs = 0
        total_fat = 0
        
        # Create 2-3 meals per day
        meal_types = random.sample(['BREAKFAST', 'LUNCH', 'DINNER', 'SNACK'], random.randint(2, 3))
        
        for meal_type in meal_types:
            meal_data = self.create_single_meal(user, date, meal_type, foods)
            total_calories += meal_data['calories']
            total_protein += meal_data['protein']
            total_carbs += meal_data['carbs']
            total_fat += meal_data['fat']
        
        # Create daily progress using get_or_create for safety
        DailyProgress.objects.get_or_create(
            user=user,
            date=date,
            defaults={
                'total_calories_consumed': round(total_calories),
                'total_protein': round(total_protein, 1),
                'total_carbs': round(total_carbs, 1),
                'total_fat': round(total_fat, 1)
            }
        )

    def create_single_meal(self, user, date, meal_type, foods):
        """Create a single meal"""
        meal = Meal.objects.create(user=user, meal_type=meal_type, date=date)
        
        total_calories = 0
        total_protein = 0
        total_carbs = 0
        total_fat = 0
        
        # Select 1-2 random foods (keep it simple)
        selected_foods = random.sample(foods, min(2, len(foods)))
        
        for food in selected_foods:
            quantity = random.uniform(0.8, 1.5)
            
            MealFoodItem.objects.create(
                meal=meal,
                food_item=food,
                quantity=round(quantity, 1)
            )
            
            total_calories += food.calories * quantity
            total_protein += food.protein * quantity
            total_carbs += food.carbs * quantity
            total_fat += food.fat * quantity
        
        return {
            'calories': total_calories,
            'protein': total_protein,
            'carbs': total_carbs,
            'fat': total_fat
        }