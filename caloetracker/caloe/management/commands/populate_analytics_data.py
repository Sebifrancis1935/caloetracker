from django.core.management.base import BaseCommand
from caloe.models import CustomUser, DailyProgress, WeightLog, WaterIntake
from django.utils import timezone
from datetime import timedelta
import random

class Command(BaseCommand):
    help = 'Populate enhanced analytics data with realistic patterns'

    def add_arguments(self, parser):
        parser.add_argument(
            '--username',
            type=str,
            help='Username to populate analytics data for',
            required=True
        )

    def handle(self, *args, **options):
        username = options['username']
        
        try:
            user = CustomUser.objects.get(username=username)
        except CustomUser.DoesNotExist:
            self.stdout.write(self.style.ERROR(f'User {username} does not exist'))
            return

        self.stdout.write(self.style.SUCCESS(f'Creating enhanced analytics data for: {username}'))

        # Create weekly patterns for more interesting graphs
        self.create_weekly_patterns(user)
        
        # Create monthly trends
        self.create_monthly_trends(user)
        
        # Create special event data (cheat days, workout days, etc.)
        self.create_special_events(user)

        self.stdout.write(self.style.SUCCESS('✅ Enhanced analytics data created!'))
        self.stdout.write(self.style.SUCCESS('📈 Graphs will now show realistic patterns and trends'))

    def create_weekly_patterns(self, user):
        """Create realistic weekly patterns in data"""
        today = timezone.now().date()
        calorie_target = user.get_daily_calorie_target()
        
        # Update last 60 days with weekly patterns
        for i in range(60):
            date = today - timedelta(days=59-i)
            weekday = date.weekday()
            
            try:
                progress = DailyProgress.objects.get(user=user, date=date)
                
                # Adjust based on day of week
                if weekday == 0:  # Monday - Start week strong
                    progress.total_calories_consumed = calorie_target * random.uniform(0.85, 0.95)
                elif weekday == 4:  # Friday - Relax a bit
                    progress.total_calories_consumed = calorie_target * random.uniform(0.95, 1.05)
                elif weekday >= 5:  # Weekend - More variation
                    progress.total_calories_consumed = calorie_target * random.uniform(0.9, 1.15)
                else:  # Tuesday-Thursday - Consistent
                    progress.total_calories_consumed = calorie_target * random.uniform(0.88, 0.98)
                
                progress.save()
                
            except DailyProgress.DoesNotExist:
                continue

    def create_monthly_trends(self, user):
        """Create monthly progress trends"""
        today = timezone.now().date()
        
        # Update weight data to show clearer trends
        weight_logs = WeightLog.objects.filter(user=user).order_by('date')
        
        if weight_logs.count() > 10:
            # Smooth out the weight data to show clearer trends
            for i in range(1, len(weight_logs)-1):
                prev_weight = weight_logs[i-1].weight
                current_weight = weight_logs[i].weight
                next_weight = weight_logs[i+1].weight
                
                # Simple smoothing
                smoothed_weight = (prev_weight + current_weight + next_weight) / 3
                weight_logs[i].weight = round(smoothed_weight, 1)
                weight_logs[i].save()

    def create_special_events(self, user):
        """Create special event days for more interesting analytics"""
        today = timezone.now().date()
        calorie_target = user.get_daily_calorie_target()
        
        # Create some special event days in the past 30 days
        special_dates = [
            today - timedelta(days=7),   # 1 week ago - Cheat day
            today - timedelta(days=14),  # 2 weeks ago - Workout day
            today - timedelta(days=21),  # 3 weeks ago - Light day
        ]
        
        for date in special_dates:
            try:
                progress = DailyProgress.objects.get(user=user, date=date)
                
                if date == today - timedelta(days=7):
                    # Cheat day - high calories
                    progress.total_calories_consumed = calorie_target * 1.4
                    progress.total_protein *= 1.2
                    progress.total_carbs *= 1.5
                    progress.total_fat *= 1.3
                elif date == today - timedelta(days=14):
                    # Workout day - high protein
                    progress.total_calories_consumed = calorie_target * 1.1
                    progress.total_protein *= 1.4
                elif date == today - timedelta(days=21):
                    # Light day - low calories
                    progress.total_calories_consumed = calorie_target * 0.7
                
                progress.save()
                
            except DailyProgress.DoesNotExist:
                continue