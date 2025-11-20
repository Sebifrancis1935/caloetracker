from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.validators import MinValueValidator, MaxValueValidator

class CustomUser(AbstractUser):
    GENDER_CHOICES = [
        ('M', 'Male'),
        ('F', 'Female'),
        ('O', 'Other'),
    ]
    
    age = models.PositiveIntegerField(null=True, blank=True)
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES, null=True, blank=True)
    height = models.FloatField(help_text="Height in cm", null=True, blank=True)
    weight = models.FloatField(help_text="Weight in kg", null=True, blank=True)
    goal = models.CharField(max_length=10, choices=[('LOSE', 'Lose Weight'), ('GAIN', 'Gain Weight'), ('MAINTAIN', 'Maintain Weight')], default='MAINTAIN')
    activity_level = models.FloatField(
        default=1.2,
        validators=[MinValueValidator(1.2), MaxValueValidator(1.9)],
        help_text="1.2: Sedentary, 1.375: Lightly active, 1.55: Moderately active, 1.725: Very active, 1.9: Extra active"
    )
    
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

class MealFoodItem(models.Model):
    meal = models.ForeignKey(Meal, on_delete=models.CASCADE, related_name='food_items')
    food_item = models.ForeignKey(FoodItem, on_delete=models.CASCADE)
    quantity = models.FloatField(default=1)  # Number of servings
    
    @property
    def total_calories(self):
        return self.food_item.calories * self.quantity

class DailyProgress(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    date = models.DateField(auto_now_add=True)
    total_calories_consumed = models.FloatField(default=0)
    
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