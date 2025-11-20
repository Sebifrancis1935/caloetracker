from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from .models import CustomUser, FoodItem, Meal

class CustomUserCreationForm(UserCreationForm):
    age = forms.IntegerField(
        min_value=1, 
        max_value=120, 
        required=True,
        widget=forms.NumberInput(attrs={'class': 'form-control'})
    )
    height = forms.FloatField(
        min_value=50, 
        max_value=250, 
        required=True,
        help_text="Height in cm",
        widget=forms.NumberInput(attrs={'class': 'form-control'})
    )
    weight = forms.FloatField(
        min_value=30, 
        max_value=300, 
        required=True,
        help_text="Weight in kg", 
        widget=forms.NumberInput(attrs={'class': 'form-control'})
    )
    
    # Set default values in the form
    goal = forms.ChoiceField(
        choices=CustomUser.GOAL_CHOICES,
        initial='MAINTAIN',  # Default to maintain weight
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    activity_level = forms.ChoiceField(
        choices=CustomUser.ACTIVITY_LEVEL_CHOICES,
        initial=1.375,  # Default to "Lightly Active" - most common
        widget=forms.Select(attrs={'class': 'form-control'})
    )

    class Meta:
        model = CustomUser
        fields = ('username', 'email', 'age', 'gender', 'height', 'weight', 'goal', 'activity_level', 'password1', 'password2')
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Set default gender if not provided
        if not self['gender'].value():
            self.fields['gender'].initial = 'O'  # Default to 'Other'

class CustomAuthenticationForm(AuthenticationForm):
    username = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Username'}))
    password = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Password'}))

class UserProfileForm(forms.ModelForm):
    class Meta:
        model = CustomUser
        fields = ('age', 'gender', 'height', 'weight', 'goal', 'activity_level')

class FoodSearchForm(forms.Form):
    search_query = forms.CharField(max_length=100, required=False, widget=forms.TextInput(attrs={
        'placeholder': 'Search for food items...',
        'class': 'form-control'
    }))

class MealForm(forms.ModelForm):
    class Meta:
        model = Meal
        fields = ('meal_type',)
        widgets = {
            'meal_type': forms.Select(attrs={'class': 'form-control'})
        }

class FoodItemForm(forms.ModelForm):
    class Meta:
        model = FoodItem
        fields = ['name', 'calories', 'protein', 'carbs', 'fat', 'serving_size']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., Banana, Chicken Breast'}),
            'calories': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.1', 'min': '0'}),
            'protein': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.1', 'min': '0'}),
            'carbs': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.1', 'min': '0'}),
            'fat': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.1', 'min': '0'}),
            'serving_size': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., 100g, 1 cup, 1 piece'}),
        }
        labels = {
            'name': 'Food Name',
            'calories': 'Calories (kcal)',
            'protein': 'Protein (g)',
            'carbs': 'Carbohydrates (g)',
            'fat': 'Fat (g)',
            'serving_size': 'Serving Size',
        }
        help_texts = {
            'serving_size': 'Specify the serving size these nutrition values represent',
        }

# Phase 1 Forms - Define these separately to avoid circular imports
class WeightLogForm(forms.ModelForm):
    class Meta:
        from .models import WeightLog  # Import here to avoid circular import
        model = WeightLog
        fields = ['weight', 'notes', 'date']
        widgets = {
            'weight': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.1', 'min': '30', 'max': '300'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Optional notes...'}),
            'date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        }
        labels = {
            'weight': 'Weight (kg)',
            'notes': 'Notes',
            'date': 'Date',
        }

class ProgressPhotoForm(forms.ModelForm):
    class Meta:
        from .models import ProgressPhoto  # Import here to avoid circular import
        model = ProgressPhoto
        fields = ['image', 'caption', 'date']
        widgets = {
            'image': forms.FileInput(attrs={'class': 'form-control'}),
            'caption': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Add a caption...'}),
            'date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        }

class WaterIntakeForm(forms.ModelForm):
    class Meta:
        from .models import WaterIntake  # Import here to avoid circular import
        model = WaterIntake
        fields = ['amount_ml']
        widgets = {
            'amount_ml': forms.NumberInput(attrs={
                'class': 'form-control', 
                'min': '50', 
                'max': '1000',
                'step': '50'
            }),
        }
        labels = {
            'amount_ml': 'Amount (ml)',
        }

class WaterGoalForm(forms.ModelForm):
    class Meta:
        from .models import WaterGoal  # Import here to avoid circular import
        model = WaterGoal
        fields = ['daily_goal_ml']
        widgets = {
            'daily_goal_ml': forms.NumberInput(attrs={
                'class': 'form-control', 
                'min': '500', 
                'max': '5000',
                'step': '100'
            }),
        }
        labels = {
            'daily_goal_ml': 'Daily Water Goal (ml)',
        }