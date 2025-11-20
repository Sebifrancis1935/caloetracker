from django.core.management.base import BaseCommand
from caloe.models import FoodItem

class Command(BaseCommand):
    help = 'Populate the database with sample food items'

    def handle(self, *args, **options):
        food_items = [
            {'name': 'Apple', 'calories': 52, 'protein': 0.3, 'carbs': 14, 'fat': 0.2, 'serving_size': '1 medium (182g)'},
            {'name': 'Banana', 'calories': 89, 'protein': 1.1, 'carbs': 23, 'fat': 0.3, 'serving_size': '1 medium (118g)'},
            {'name': 'Chicken Breast', 'calories': 165, 'protein': 31, 'carbs': 0, 'fat': 3.6, 'serving_size': '100g cooked'},
            {'name': 'White Rice', 'calories': 130, 'protein': 2.7, 'carbs': 28, 'fat': 0.3, 'serving_size': '1 cup cooked'},
            {'name': 'Brown Rice', 'calories': 112, 'protein': 2.6, 'carbs': 23, 'fat': 0.8, 'serving_size': '1 cup cooked'},
            {'name': 'Egg', 'calories': 72, 'protein': 6.3, 'carbs': 0.6, 'fat': 4.8, 'serving_size': '1 large (50g)'},
            {'name': 'Whole Milk', 'calories': 61, 'protein': 3.2, 'carbs': 4.8, 'fat': 3.3, 'serving_size': '100ml'},
            {'name': 'Oatmeal', 'calories': 68, 'protein': 2.4, 'carbs': 12, 'fat': 1.4, 'serving_size': '100g cooked'},
            {'name': 'Bread', 'calories': 265, 'protein': 9, 'carbs': 49, 'fat': 3.2, 'serving_size': '100g'},
            {'name': 'Salmon', 'calories': 208, 'protein': 20, 'carbs': 0, 'fat': 13, 'serving_size': '100g cooked'},
            {'name': 'Broccoli', 'calories': 34, 'protein': 2.8, 'carbs': 7, 'fat': 0.4, 'serving_size': '100g'},
            {'name': 'Potato', 'calories': 77, 'protein': 2, 'carbs': 17, 'fat': 0.1, 'serving_size': '100g'},
            {'name': 'Pasta', 'calories': 131, 'protein': 5, 'carbs': 25, 'fat': 1.1, 'serving_size': '100g cooked'},
            {'name': 'Yogurt', 'calories': 61, 'protein': 3.5, 'carbs': 4.7, 'fat': 3.3, 'serving_size': '100g'},
            {'name': 'Cheese', 'calories': 402, 'protein': 25, 'carbs': 1.3, 'fat': 33, 'serving_size': '100g'},
            {'name': 'Almonds', 'calories': 579, 'protein': 21, 'carbs': 22, 'fat': 50, 'serving_size': '100g'},
            {'name': 'Orange', 'calories': 47, 'protein': 0.9, 'carbs': 12, 'fat': 0.1, 'serving_size': '1 medium (131g)'},
            {'name': 'Beef Steak', 'calories': 271, 'protein': 26, 'carbs': 0, 'fat': 18, 'serving_size': '100g cooked'},
            {'name': 'Tuna', 'calories': 132, 'protein': 29, 'carbs': 0, 'fat': 1.2, 'serving_size': '100g canned'},
            {'name': 'Avocado', 'calories': 160, 'protein': 2, 'carbs': 9, 'fat': 15, 'serving_size': '100g'},
        ]
        
        created_count = 0
        for food_data in food_items:
            obj, created = FoodItem.objects.get_or_create(
                name=food_data['name'],
                defaults=food_data
            )
            if created:
                created_count += 1
        
        self.stdout.write(
            self.style.SUCCESS(f'Successfully populated {created_count} food items')
        )