from django.core.management.base import BaseCommand
from caloe.models import CustomUser, FoodItem, Meal, MealFoodItem, DailyProgress, WeightLog, WaterIntake, WaterGoal, ProgressPhoto
from django.utils import timezone
from datetime import timedelta
import random

class Command(BaseCommand):
    help = 'Create fresh sample data without any conflicts'

    def add_arguments(self, parser):
        parser.add_argument('username', type=str)

    def handle(self, *args, **options):
        username = options['username']
        
        try:
            user = CustomUser.objects.get(username=username)
        except CustomUser.DoesNotExist:
            self.stdout.write(self.style.ERROR(f'User {username} does not exist'))
            return

        self.stdout.write(self.style.SUCCESS(f'Creating fresh data for: {username}'))

        # Get food items
        foods = list(FoodItem.objects.all())
        if not foods:
            self.stdout.write(self.style.ERROR('No food items found. Run populate_food_items first.'))
            return

        # Set water goal
        WaterGoal.objects.get_or_create(user=user, defaults={'daily_goal_ml': 2500})

        # Create data for last 30 days
        today = timezone.now().date()
        
        for day in range(30):
            date = today - timedelta(days=29-day)
            self.stdout.write(f'Creating data for {date}...')
            
            # Create weight data
            self.create_weight_for_day(user, date, day)
            
            # Create water data
            self.create_water_for_day(user, date)
            
            # Create meals and progress
            self.create_meals_and_progress(user, date, foods)
        
        self.stdout.write(self.style.SUCCESS('✅ Fresh data created successfully!'))
        self.stdout.write(self.style.SUCCESS('🎉 You can now view graphs and analytics!'))

    def create_weight_for_day(self, user, date, day):
        """Create weight data for a specific day"""
        base_weight = user.weight or 75.0
        
        # Create realistic trend based on goal
        if user.goal == 'LOSE':
            trend = -0.08  # Lose weight slowly
            weight = base_weight - (day * trend) + random.uniform(-0.3, 0.3)
        elif user.goal == 'GAIN':
            trend = 0.06  # Gain weight slowly
            weight = base_weight + (day * trend) + random.uniform(-0.3, 0.3)
        else:  # MAINTAIN
            weight = base_weight + random.uniform(-0.5, 0.5)
        
        WeightLog.objects.create(
            user=user,
            date=date,
            weight=round(weight, 1),
            notes=self.get_weight_note(date)
        )

    def get_weight_note(self, date):
        """Simple weight notes"""
        notes = ["Morning check", "Daily weigh-in", "Progress tracking"]
        return random.choice(notes)

    def create_water_for_day(self, user, date):
        """Create water intake for a specific day"""
        # Create 3-5 water entries per day
        for i in range(random.randint(3, 5)):
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
        
        # Meal types to create
        meal_types = ['BREAKFAST', 'LUNCH', 'DINNER']
        if random.random() > 0.4:  # 60% chance of snack
            meal_types.append('SNACK')
        
        for meal_type in meal_types:
            meal_data = self.create_single_meal(user, date, meal_type, foods)
            total_calories += meal_data['calories']
            total_protein += meal_data['protein']
            total_carbs += meal_data['carbs']
            total_fat += meal_data['fat']
        
        # Create daily progress
        DailyProgress.objects.create(
            user=user,
            date=date,
            total_calories_consumed=round(total_calories),
            total_protein=round(total_protein, 1),
            total_carbs=round(total_carbs, 1),
            total_fat=round(total_fat, 1)
        )

    def create_single_meal(self, user, date, meal_type, foods):
        """Create a single meal"""
        meal = Meal.objects.create(user=user, meal_type=meal_type, date=date)
        
        total_calories = 0
        total_protein = 0
        total_carbs = 0
        total_fat = 0
        
        # Select 2-3 random foods
        selected_foods = random.sample(foods, min(3, len(foods)))
        
        for food in selected_foods:
            quantity = random.uniform(0.5, 2.0)
            
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