from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from .models import CustomUser, FoodItem, Meal

class CustomUserCreationForm(UserCreationForm):
    age = forms.IntegerField(min_value=1, max_value=120, required=True)
    height = forms.FloatField(min_value=50, max_value=250, required=True, help_text="Height in cm")
    weight = forms.FloatField(min_value=30, max_value=300, required=True, help_text="Weight in kg")
    
    class Meta:
        model = CustomUser
        fields = ('username', 'email', 'age', 'gender', 'height', 'weight', 'goal', 'activity_level', 'password1', 'password2')

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

# ADD THIS NEW FORM
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