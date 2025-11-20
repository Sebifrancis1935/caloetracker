from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone  # ADD THIS IMPORT

class CustomUser(AbstractUser):
    GENDER_CHOICES = [
        ('M', 'Male'),
        ('F', 'Female'),
        ('O', 'Other'),
    ]
    
    GOAL_CHOICES = [
        ('LOSE', 'Lose Weight'),
        ('GAIN', 'Gain Weight'),
        ('MAINTAIN', 'Maintain Weight'),
    ]
    
    ACTIVITY_LEVEL_CHOICES = [
        (1.2, 'Sedentary (little or no exercise)'),
        (1.375, 'Lightly active (light exercise 1-3 days/week)'),
        (1.55, 'Moderately active (moderate exercise 3-5 days/week)'),
        (1.725, 'Very active (hard exercise 6-7 days/week)'),
        (1.9, 'Extra active (very hard exercise & physical job)'),
    ]
    
    age = models.PositiveIntegerField(null=True, blank=True)
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES, null=True, blank=True)
    height = models.FloatField(help_text="Height in cm", null=True, blank=True)
    weight = models.FloatField(help_text="Weight in kg", null=True, blank=True)
    goal = models.CharField(max_length=10, choices=GOAL_CHOICES, default='MAINTAIN')
    activity_level = models.FloatField(
        default=1.2,
        choices=ACTIVITY_LEVEL_CHOICES,
        validators=[MinValueValidator(1.2), MaxValueValidator(1.9)],
        help_text="Activity level multiplier for calorie calculation"
    )
    
    # Add macro goals for Phase 1
    protein_goal = models.FloatField(default=0, help_text="Protein goal in grams")
    carbs_goal = models.FloatField(default=0, help_text="Carbs goal in grams")
    fat_goal = models.FloatField(default=0, help_text="Fat goal in grams")
    
    def calculate_bmr(self):
        """Calculate Basal Metabolic Rate"""
        if self.gender == 'M':
            return 88.362 + (13.397 * self.weight) + (4.799 * self.height) - (5.677 * self.age)
        elif self.gender == 'F':
            return 447.593 + (9.247 * self.weight) + (3.098 * self.height) - (4.330 * self.age)
        else:
            # Average of male and female formula for 'Other'
            male_bmr = 88.362 + (13.397 * self.weight) + (4.799 * self.height) - (5.677 * self.age)
            female_bmr = 447.593 + (9.247 * self.weight) + (3.098 * self.height) - (4.330 * self.age)
            return (male_bmr + female_bmr) / 2
    
    def calculate_maintenance_calories(self):
        """Calculate daily maintenance calories"""
        bmr = self.calculate_bmr()
        return round(bmr * self.activity_level)
    
    def get_daily_calorie_target(self):
        """Get daily calorie target based on goal"""
        maintenance = self.calculate_maintenance_calories()
        
        if self.goal == 'LOSE':
            return maintenance - 500  # 500 calorie deficit for weight loss
        elif self.goal == 'GAIN':
            return maintenance + 500  # 500 calorie surplus for weight gain
        else:
            return maintenance

    def calculate_macro_goals(self):
        """Calculate default macro goals based on calorie target"""
        calories = self.get_daily_calorie_target()
        if not self.protein_goal:
            self.protein_goal = round((calories * 0.3) / 4)  # 30% from protein
        if not self.carbs_goal:
            self.carbs_goal = round((calories * 0.4) / 4)   # 40% from carbs
        if not self.fat_goal:
            self.fat_goal = round((calories * 0.3) / 9)     # 30% from fat
        self.save()

    def __str__(self):
        return self.username

class FoodItem(models.Model):
    name = models.CharField(max_length=200)
    calories = models.FloatField()
    protein = models.FloatField(default=0)
    carbs = models.FloatField(default=0)
    fat = models.FloatField(default=0)
    serving_size = models.CharField(max_length=100, default="100g")
    created_by = models.ForeignKey(CustomUser, on_delete=models.CASCADE, null=True, blank=True)
    is_custom = models.BooleanField(default=False)  # To distinguish system vs custom items
    
    def __str__(self):
        return f"{self.name} ({self.calories} kcal)"

class Meal(models.Model):
    MEAL_TYPES = [
        ('BREAKFAST', 'Breakfast'),
        ('LUNCH', 'Lunch'),
        ('DINNER', 'Dinner'),
        ('SNACK', 'Snack'),
    ]
    
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    meal_type = models.CharField(max_length=10, choices=MEAL_TYPES)
    date = models.DateField(auto_now_add=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    @property
    def total_calories(self):
        return sum(item.total_calories for item in self.food_items.all())
    
    def __str__(self):
        return f"{self.user.username} - {self.meal_type} - {self.date}"

class MealFoodItem(models.Model):
    meal = models.ForeignKey(Meal, on_delete=models.CASCADE, related_name='food_items')
    food_item = models.ForeignKey(FoodItem, on_delete=models.CASCADE)
    quantity = models.FloatField(default=1)  # Number of servings
    
    @property
    def total_calories(self):
        return self.food_item.calories * self.quantity
    
    def __str__(self):
        return f"{self.food_item.name} in {self.meal}"

class DailyProgress(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    date = models.DateField(auto_now_add=True)
    total_calories_consumed = models.FloatField(default=0)
    # Add macro fields for Phase 1
    total_protein = models.FloatField(default=0)
    total_carbs = models.FloatField(default=0)
    total_fat = models.FloatField(default=0)
    
    class Meta:
        unique_together = ['user', 'date']
    
    def calories_remaining(self):
        target = self.user.get_daily_calorie_target()
        return max(0, target - self.total_calories_consumed)
    
    def progress_percentage(self):
        target = self.user.get_daily_calorie_target()
        if target == 0:
            return 0
        return min(100, (self.total_calories_consumed / target) * 100)
    
    # Add macro methods for Phase 1
    def protein_remaining(self):
        return max(0, self.user.protein_goal - self.total_protein)
    
    def carbs_remaining(self):
        return max(0, self.user.carbs_goal - self.total_carbs)
    
    def fat_remaining(self):
        return max(0, self.user.fat_goal - self.total_fat)
    
    def protein_percentage(self):
        if self.user.protein_goal == 0:
            return 0
        return min(100, (self.total_protein / self.user.protein_goal) * 100)
    
    def carbs_percentage(self):
        if self.user.carbs_goal == 0:
            return 0
        return min(100, (self.total_carbs / self.user.carbs_goal) * 100)
    
    def fat_percentage(self):
        if self.user.fat_goal == 0:
            return 0
        return min(100, (self.total_fat / self.user.fat_goal) * 100)
    
    def __str__(self):
        return f"{self.user.username} - {self.date} - {self.total_calories_consumed} kcal"

# Phase 1: Weight Tracking
class WeightLog(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    date = models.DateField(default=timezone.now)  # Now timezone is imported
    weight = models.FloatField(help_text="Weight in kg")
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['user', 'date']
        ordering = ['-date']
    
    def __str__(self):
        return f"{self.user.username} - {self.weight}kg - {self.date}"

# Phase 1: Progress Photos
class ProgressPhoto(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    date = models.DateField(default=timezone.now)
    image = models.ImageField(upload_to='progress_photos/')
    caption = models.CharField(max_length=200, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-date']
    
    def __str__(self):
        return f"{self.user.username} - {self.date}"

# Phase 1: Water Intake Tracking
class WaterIntake(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    date = models.DateField(default=timezone.now)
    amount_ml = models.IntegerField(help_text="Amount in milliliters")
    time = models.TimeField(auto_now_add=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-date', '-time']
    
    def __str__(self):
        return f"{self.user.username} - {self.amount_ml}ml - {self.date}"

class WaterGoal(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE)
    daily_goal_ml = models.IntegerField(default=2000, help_text="Daily water goal in ml")
    
    def __str__(self):
        return f"{self.user.username} - {self.daily_goal_ml}ml"