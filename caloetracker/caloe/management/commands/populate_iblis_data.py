from django.core.management.base import BaseCommand
from caloe.models import CustomUser, FoodItem, Meal, MealFoodItem, DailyProgress, WeightLog, WaterIntake, WaterGoal, ProgressPhoto
from django.utils import timezone
from datetime import timedelta
import random

class Command(BaseCommand):
    help = 'Create 3 months of comprehensive data for user Iblis'

    def handle(self, *args, **options):
        # Get or create user Iblis
        user, created = CustomUser.objects.get_or_create(
            username='Iblis',
            defaults={
                'email': 'iblis@caloetracker.com',
                'age': 32,
                'gender': 'M',
                'height': 180,
                'weight': 85,
                'goal': 'LOSE',
                'activity_level': 1.55,
            }
        )
        
        if created:
            user.set_password('Iblis@123')
            user.save()

        self.stdout.write(self.style.SUCCESS(f'🎯 Creating 3 months of data for: {user.username}'))

        # Get food items
        foods = list(FoodItem.objects.all())
        if not foods:
            self.stdout.write(self.style.ERROR('❌ No food items found. Run populate_food_items first.'))
            return

        # Set water goal
        WaterGoal.objects.get_or_create(user=user, defaults={'daily_goal_ml': 3000})

        # Create 90 days of data (3 months)
        today = timezone.now().date()
        days_to_create = 90
        
        # Categorize foods for realistic meals
        breakfast_foods = [f for f in foods if any(x in f.name.lower() for x in 
                          ['oatmeal', 'yogurt', 'bread', 'banana', 'almond', 'egg', 'milk', 'protein'])]
        lunch_foods = [f for f in foods if any(x in f.name.lower() for x in 
                      ['chicken', 'rice', 'salad', 'broccoli', 'salmon', 'quinoa', 'vegetable', 'dal'])]
        dinner_foods = [f for f in foods if any(x in f.name.lower() for x in 
                       ['beef', 'pasta', 'fish', 'curry', 'paneer', 'sweet potato', 'asparagus'])]
        snack_foods = [f for f in foods if any(x in f.name.lower() for x in 
                      ['apple', 'shake', 'carrot', 'tea', 'coffee', 'nuts', 'peanut'])]

        successful_days = 0
        
        for day in range(days_to_create):
            date = today - timedelta(days=days_to_create-1-day)
            
            try:
                if day % 30 == 0:
                    self.stdout.write(f'📅 Creating month {day//30 + 1} data...')
                
                # Create weight data with realistic weight loss trend
                self.create_weight_data(user, date, day, days_to_create)
                
                # Create comprehensive water data
                self.create_water_data(user, date)
                
                # Create full day of meals
                meal_data = self.create_daily_meals(user, date, breakfast_foods, lunch_foods, dinner_foods, snack_foods)
                
                # Create daily progress using update_or_create to handle duplicates
                self.create_daily_progress(user, date, day, meal_data)
                
                successful_days += 1
                self.stdout.write(self.style.SUCCESS(f'   ✅ Created data for {date}'))
                
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'   ❌ Error for {date}: {str(e)}'))
                # Try alternative approach for failed dates
                try:
                    self.alternative_approach(user, date, day, days_to_create, breakfast_foods, lunch_foods, dinner_foods, snack_foods)
                    successful_days += 1
                    self.stdout.write(self.style.SUCCESS(f'   ✅ Recovered data for {date}'))
                except Exception as e2:
                    self.stdout.write(self.style.ERROR(f'   ❌ Recovery failed for {date}: {str(e2)}'))

        # Create progress photo entries
        self.create_progress_photos(user, today)
        
        # Set macro goals
        user.calculate_macro_goals()
        user.save()

        self.stdout.write(self.style.SUCCESS(f'\n🎉 SUCCESS! Created {successful_days} days of comprehensive data!'))
        self.stdout.write(self.style.SUCCESS('📊 3 months of weight, nutrition, and activity data ready!'))
        self.stdout.write(self.style.SUCCESS('📈 Analytics will show complete progress history!'))

    def alternative_approach(self, user, date, day, total_days, breakfast_foods, lunch_foods, dinner_foods, snack_foods):
        """Alternative approach for dates that failed with the main method"""
        # Use update_or_create for all models
        self.create_weight_data_alternative(user, date, day, total_days)
        self.create_water_data_alternative(user, date)
        meal_data = self.create_daily_meals_alternative(user, date, breakfast_foods, lunch_foods, dinner_foods, snack_foods)
        self.create_daily_progress_alternative(user, date, day, meal_data)

    def create_weight_data(self, user, date, day, total_days):
        """Create realistic weight loss progression"""
        start_weight = 88.0
        target_weight = 78.0
        
        progress = day / total_days
        base_weight = start_weight - (progress * (start_weight - target_weight))
        fluctuation = random.uniform(-0.8, 0.8)
        weight = base_weight + fluctuation
        
        if date.weekday() >= 5:
            weight += random.uniform(0.3, 0.7)
        
        # Use update_or_create to handle duplicates
        WeightLog.objects.update_or_create(
            user=user,
            date=date,
            defaults={
                'weight': round(weight, 1),
                'notes': self.get_weight_note(date, weight, start_weight)
            }
        )

    def create_weight_data_alternative(self, user, date, day, total_days):
        """Alternative weight data creation"""
        start_weight = 88.0
        target_weight = 78.0
        
        progress = day / total_days
        base_weight = start_weight - (progress * (start_weight - target_weight))
        fluctuation = random.uniform(-0.8, 0.8)
        weight = base_weight + fluctuation
        
        if date.weekday() >= 5:
            weight += random.uniform(0.3, 0.7)
        
        # Delete and create fresh
        WeightLog.objects.filter(user=user, date=date).delete()
        WeightLog.objects.create(
            user=user,
            date=date,
            weight=round(weight, 1),
            notes=self.get_weight_note(date, weight, start_weight)
        )

    def get_weight_note(self, date, weight, start_weight):
        """Generate realistic weight notes"""
        monthly_milestones = {
            30: "🎉 First month complete! Good progress!",
            60: "🎉 Two months down! Halfway to goal!",
            89: "🎉 Three months complete! Goal achieved!"
        }
        
        day_of_month = date.day
        if day_of_month in monthly_milestones:
            return monthly_milestones[day_of_month]
        
        notes = [
            "Morning weigh-in", "Before breakfast", "Weekly progress check",
            "After workout session", "Consistent tracking", "Monthly measurement"
        ]
        return random.choice(notes)

    def create_water_data(self, user, date):
        """Create comprehensive water intake data"""
        # Clear existing water data for this date
        WaterIntake.objects.filter(user=user, date=date).delete()
        
        if date.weekday() < 5:
            amounts = [400, 300, 500, 350, 450]
        else:
            amounts = [500, 400, 600, 300]
        
        for amount in amounts:
            WaterIntake.objects.create(
                user=user,
                date=date,
                amount_ml=amount
            )

    def create_water_data_alternative(self, user, date):
        """Alternative water data creation"""
        self.create_water_data(user, date)  # Same method works

    def create_daily_meals(self, user, date, breakfast_foods, lunch_foods, dinner_foods, snack_foods):
        """Create a full day of realistic meals"""
        # Clear existing meals for this date
        Meal.objects.filter(user=user, date=date).delete()
        
        return self._create_meals_logic(user, date, breakfast_foods, lunch_foods, dinner_foods, snack_foods)

    def create_daily_meals_alternative(self, user, date, breakfast_foods, lunch_foods, dinner_foods, snack_foods):
        """Alternative meal creation"""
        return self.create_daily_meals(user, date, breakfast_foods, lunch_foods, dinner_foods, snack_foods)

    def _create_meals_logic(self, user, date, breakfast_foods, lunch_foods, dinner_foods, snack_foods):
        """Shared logic for creating meals"""
        total_calories = 0
        total_protein = 0
        total_carbs = 0
        total_fat = 0
        
        # Breakfast
        breakfast_data = self.create_meal(user, date, 'BREAKFAST', breakfast_foods, 2, 3)
        total_calories += breakfast_data['calories']
        total_protein += breakfast_data['protein']
        total_carbs += breakfast_data['carbs']
        total_fat += breakfast_data['fat']

        # Lunch
        lunch_data = self.create_meal(user, date, 'LUNCH', lunch_foods, 2, 4)
        total_calories += lunch_data['calories']
        total_protein += lunch_data['protein']
        total_carbs += lunch_data['carbs']
        total_fat += lunch_data['fat']

        # Dinner
        dinner_data = self.create_meal(user, date, 'DINNER', dinner_foods, 2, 4)
        total_calories += dinner_data['calories']
        total_protein += dinner_data['protein']
        total_carbs += dinner_data['carbs']
        total_fat += dinner_data['fat']

        # Snacks
        if random.random() < 0.8:
            snack_data = self.create_meal(user, date, 'SNACK', snack_foods, 1, 2)
            total_calories += snack_data['calories']
            total_protein += snack_data['protein']
            total_carbs += snack_data['carbs']
            total_fat += snack_data['fat']

        return {
            'calories': total_calories,
            'protein': total_protein,
            'carbs': total_carbs,
            'fat': total_fat
        }

    def create_meal(self, user, date, meal_type, available_foods, min_items, max_items):
        """Create a realistic meal"""
        meal = Meal.objects.create(user=user, meal_type=meal_type, date=date)
        
        total_calories = 0
        total_protein = 0
        total_carbs = 0
        total_fat = 0
        
        num_items = random.randint(min_items, max_items)
        selected_foods = random.sample(available_foods, min(num_items, len(available_foods)))
        
        for food in selected_foods:
            if food.calories > 200:
                quantity = random.uniform(0.3, 0.8)
            elif food.calories > 100:
                quantity = random.uniform(0.5, 1.5)
            else:
                quantity = random.uniform(1.0, 3.0)
            
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

    def create_daily_progress(self, user, date, day, meal_data):
        """Create daily progress entry using update_or_create"""
        total_calories = meal_data['calories']
        total_protein = meal_data['protein']
        total_carbs = meal_data['carbs']
        total_fat = meal_data['fat']
        
        if user.goal == 'LOSE':
            if day % 7 == 0:
                total_calories *= 1.3
            elif random.random() < 0.8:
                total_calories *= 0.9

        # Use update_or_create to handle duplicates
        DailyProgress.objects.update_or_create(
            user=user,
            date=date,
            defaults={
                'total_calories_consumed': round(total_calories),
                'total_protein': round(total_protein, 1),
                'total_carbs': round(total_carbs, 1),
                'total_fat': round(total_fat, 1)
            }
        )

    def create_daily_progress_alternative(self, user, date, day, meal_data):
        """Alternative daily progress creation"""
        total_calories = meal_data['calories']
        total_protein = meal_data['protein']
        total_carbs = meal_data['carbs']
        total_fat = meal_data['fat']
        
        if user.goal == 'LOSE':
            if day % 7 == 0:
                total_calories *= 1.3
            elif random.random() < 0.8:
                total_calories *= 0.9

        # Delete and create fresh
        DailyProgress.objects.filter(user=user, date=date).delete()
        DailyProgress.objects.create(
            user=user,
            date=date,
            total_calories_consumed=round(total_calories),
            total_protein=round(total_protein, 1),
            total_carbs=round(total_carbs, 1),
            total_fat=round(total_fat, 1)
        )

    def create_progress_photos(self, user, today):
        """Create progress photo entries"""
        ProgressPhoto.objects.filter(user=user).delete()
        
        for i in range(4):
            date = today - timedelta(days=30 * i)
            ProgressPhoto.objects.create(
                user=user,
                date=date,
                caption=f'Month {i+1} Progress - Weight tracking'
            )