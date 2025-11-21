from django.core.management.base import BaseCommand
from caloe.models import CustomUser, FoodItem, Meal, MealFoodItem, DailyProgress, WeightLog, WaterIntake, WaterGoal, ProgressPhoto
from django.utils import timezone
from datetime import timedelta
import random
import os
from django.core.files import File

class Command(BaseCommand):
    help = 'Populate comprehensive sample data for current user'

    def add_arguments(self, parser):
        parser.add_argument(
            '--username',
            type=str,
            help='Username to populate data for',
            required=True
        )

    def handle(self, *args, **options):
        username = options['username']
        
        try:
            user = CustomUser.objects.get(username=username)
        except CustomUser.DoesNotExist:
            self.stdout.write(self.style.ERROR(f'User {username} does not exist'))
            return

        self.stdout.write(self.style.SUCCESS(f'Populating data for user: {username}'))

        # Get all food items
        foods = list(FoodItem.objects.all())
        if not foods:
            self.stdout.write(self.style.ERROR('No food items found. Run populate_food_items first.'))
            return

        # Calculate user's calorie target for realistic data
        calorie_target = user.get_daily_calorie_target()
        
        # Create weight logs (last 90 days with realistic progression)
        self.create_weight_data(user, 90)
        
        # Create water goals and intake data
        self.create_water_data(user, 90)
        
        # Create meals and daily progress (last 30 days)
        self.create_meal_progress_data(user, foods, calorie_target, 30)
        
        # Create progress photos (sample entries)
        self.create_progress_photos(user)
        
        # Calculate and set macro goals if not set
        if not user.protein_goal:
            user.calculate_macro_goals()
            user.save()

        self.stdout.write(self.style.SUCCESS('✅ Successfully created comprehensive sample data!'))
        self.stdout.write(self.style.SUCCESS('📊 Includes: 90 days weight logs, 30 days meals, water intake, progress photos'))
        self.stdout.write(self.style.SUCCESS('📈 Analytics and graphs will now show realistic data'))

    def create_weight_data(self, user, days):
        """Create realistic weight progression data"""
        self.stdout.write('Creating weight logs...')
        
        today = timezone.now().date()
        base_weight = user.weight or 75.0
        
        # Create realistic weight loss/gain based on user goal
        if user.goal == 'LOSE':
            trend = -0.1  # Lose 0.1kg per day on average
        elif user.goal == 'GAIN':
            trend = 0.08  # Gain 0.08kg per day on average
        else:
            trend = 0.0   # Maintain weight
        
        for i in range(days):
            date = today - timedelta(days=days-1-i)
            
            # Calculate base weight with trend
            trend_weight = base_weight + (trend * i)
            
            # Add realistic daily fluctuations
            daily_fluctuation = random.uniform(-0.5, 0.5)
            weight = trend_weight + daily_fluctuation
            
            # Create some pattern (lower weight on weekdays, higher on weekends)
            if date.weekday() >= 5:  # Weekend
                weight += random.uniform(0.2, 0.5)
            
            WeightLog.objects.get_or_create(
                user=user,
                date=date,
                defaults={
                    'weight': round(weight, 1),
                    'notes': self.get_weight_note(date, weight, base_weight)
                }
            )

    def get_weight_note(self, date, weight, base_weight):
        """Generate realistic weight log notes"""
        notes = [
            "Morning weigh-in", "Before breakfast", "Evening check",
            "After workout", "Weekly measurement", "Monthly progress check"
        ]
        
        special_notes = [
            "Feeling lighter today!", "Good progress this week",
            "Stayed consistent with diet", "Increased water intake",
            "Reduced sodium intake", "Good sleep quality"
        ]
        
        if date.weekday() == 0:  # Monday
            return random.choice(special_notes)
        elif random.random() < 0.2:  # 20% chance of special note
            return random.choice(special_notes)
        else:
            return random.choice(notes)

    def create_water_data(self, user, days):
        """Create realistic water intake data"""
        self.stdout.write('Creating water data...')
        
        today = timezone.now().date()
        
        # Set water goal
        water_goal, _ = WaterGoal.objects.get_or_create(
            user=user,
            defaults={'daily_goal_ml': 2500}
        )

        for i in range(days):
            date = today - timedelta(days=days-1-i)
            
            # Create 3-6 water intake entries per day
            water_entries = random.randint(3, 6)
            total_daily_water = 0
            
            for j in range(water_entries):
                # Different amounts at different times
                if j == 0:  # Morning
                    amount = random.choice([300, 400, 500])
                elif j == water_entries - 1:  # Evening
                    amount = random.choice([250, 300, 350])
                else:  # Daytime
                    amount = random.choice([200, 250, 300, 400])
                
                WaterIntake.objects.create(
                    user=user,
                    date=date,
                    amount_ml=amount
                )
                total_daily_water += amount
            
            # Ensure some days meet water goal, some don't
            if total_daily_water < water_goal.daily_goal_ml and random.random() < 0.3:
                # Add extra water entry to meet goal
                extra_needed = water_goal.daily_goal_ml - total_daily_water
                if extra_needed > 0:
                    WaterIntake.objects.create(
                        user=user,
                        date=date,
                        amount_ml=min(500, extra_needed)
                    )

    def create_meal_progress_data(self, user, foods, calorie_target, days):
        """Create realistic meal and progress data"""
        self.stdout.write('Creating meal and progress data...')
        
        today = timezone.now().date()
        
        # Categorize foods
        breakfast_foods = [f for f in foods if any(x in f.name.lower() for x in ['oatmeal', 'yogurt', 'bread', 'banana', 'almond', 'egg', 'milk'])]
        lunch_foods = [f for f in foods if any(x in f.name.lower() for x in ['chicken', 'rice', 'salad', 'broccoli', 'salmon', 'quinoa'])]
        dinner_foods = [f for f in foods if any(x in f.name.lower() for x in ['beef', 'pasta', 'fish', 'curry', 'paneer', 'dal'])]
        snack_foods = [f for f in foods if any(x in f.name.lower() for x in ['apple', 'protein', 'shake', 'carrot', 'tea', 'coffee'])]

        for i in range(days):
            date = today - timedelta(days=days-1-i)
            
            daily_calories = 0
            daily_protein = 0
            daily_carbs = 0
            daily_fat = 0
            
            # Breakfast (25% of daily calories)
            breakfast_cals_target = calorie_target * 0.25
            breakfast_data = self.create_meal(
                user, date, 'BREAKFAST', breakfast_foods, 
                breakfast_cals_target, 0.8, 1.2  # 80-120% of target
            )
            daily_calories += breakfast_data['calories']
            daily_protein += breakfast_data['protein']
            daily_carbs += breakfast_data['carbs']
            daily_fat += breakfast_data['fat']

            # Lunch (35% of daily calories)
            lunch_cals_target = calorie_target * 0.35
            lunch_data = self.create_meal(
                user, date, 'LUNCH', lunch_foods,
                lunch_cals_target, 0.7, 1.1  # 70-110% of target
            )
            daily_calories += lunch_data['calories']
            daily_protein += lunch_data['protein']
            daily_carbs += lunch_data['carbs']
            daily_fat += lunch_data['fat']

            # Dinner (30% of daily calories)
            dinner_cals_target = calorie_target * 0.30
            dinner_data = self.create_meal(
                user, date, 'DINNER', dinner_foods,
                dinner_cals_target, 0.8, 1.3  # 80-130% of target
            )
            daily_calories += dinner_data['calories']
            daily_protein += dinner_data['protein']
            daily_carbs += dinner_data['carbs']
            daily_fat += dinner_data['fat']

            # Snack (10% of daily calories) - 60% chance
            if random.random() < 0.6:
                snack_cals_target = calorie_target * 0.10
                snack_data = self.create_meal(
                    user, date, 'SNACK', snack_foods,
                    snack_cals_target, 0.5, 1.5  # 50-150% of target
                )
                daily_calories += snack_data['calories']
                daily_protein += snack_data['protein']
                daily_carbs += snack_data['carbs']
                daily_fat += snack_data['fat']

            # Adjust calories based on user goal with some randomness
            if user.goal == 'LOSE':
                # Sometimes overeat, sometimes undereat
                if random.random() < 0.7:  # 70% of days are good
                    daily_calories = min(daily_calories, calorie_target * random.uniform(0.8, 0.95))
                else:  # 30% cheat days
                    daily_calories = calorie_target * random.uniform(1.0, 1.2)
            elif user.goal == 'GAIN':
                # Usually exceed target
                daily_calories = calorie_target * random.uniform(1.05, 1.25)
            else:  # MAINTAIN
                daily_calories = calorie_target * random.uniform(0.9, 1.1)

            # Create daily progress
            DailyProgress.objects.get_or_create(
                user=user,
                date=date,
                defaults={
                    'total_calories_consumed': round(daily_calories),
                    'total_protein': round(daily_protein, 1),
                    'total_carbs': round(daily_carbs, 1),
                    'total_fat': round(daily_fat, 1)
                }
            )

    def create_meal(self, user, date, meal_type, available_foods, target_calories, min_multiplier, max_multiplier):
        """Create a realistic meal with multiple food items"""
        meal = Meal.objects.create(user=user, meal_type=meal_type, date=date)
        
        total_calories = 0
        total_protein = 0
        total_carbs = 0
        total_fat = 0
        
        # Select 2-4 food items for the meal
        num_items = random.randint(2, 4)
        selected_foods = random.sample(available_foods, min(num_items, len(available_foods)))
        
        for food in selected_foods:
            # Calculate quantity to get close to target calories
            remaining_calories = (target_calories * random.uniform(min_multiplier, max_multiplier)) - total_calories
            if remaining_calories <= 0:
                break
                
            # Reasonable quantity based on food type
            if food.calories > 0:
                max_quantity = min(3.0, remaining_calories / food.calories)
                quantity = random.uniform(0.5, max_quantity)
            else:
                quantity = 1.0
            
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

    def create_progress_photos(self, user):
        """Create sample progress photo entries"""
        self.stdout.write('Creating progress photo entries...')
        
        today = timezone.now().date()
        
        # Create photo entries for the last 3 months
        for i in range(3):
            date = today - timedelta(days=30 * (i + 1))
            
            ProgressPhoto.objects.get_or_create(
                user=user,
                date=date,
                defaults={
                    'caption': f'Progress check - Month {i + 1}',
                    # Note: We can't create actual image files in management command
                    # In real scenario, you'd upload actual images
                }
            )
        
        self.stdout.write(self.style.WARNING('⚠️  Progress photos created as entries. Actual images need to be uploaded manually.'))