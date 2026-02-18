from django.db import migrations

def create_initial_plans(apps, schema_editor):
    SubscriptionPlan = apps.get_model('subscriptions', 'SubscriptionPlan')
    UserSubscription = apps.get_model('subscriptions', 'UserSubscription')
    User = apps.get_model('users', 'CustomUser')  # Start with CustomUser

    # 1. Create Plans
    basic_plan, _ = SubscriptionPlan.objects.get_or_create(
        name='BASIC',
        defaults={
            'price': 0.00,
            'max_accounts': 1,
            'max_shared_accounts': 0,
            'pdf_export_limit': 5,
            'can_export_csv': False,
            'has_advanced_analytics': False,
            'has_team_collaboration': False,
            'has_basic_app_features': True,
        }
    )

    SubscriptionPlan.objects.get_or_create(
        name='PLUS',
        defaults={
            'price': 9.99,
            'max_accounts': None,  # Unlimited? Or specific limit? user prompt says "Multiple accounts". let's say 5 for now or unlimited. Prompt says "Multiple accounts" for Plus, "Unlimited accounts" for Pro. Maybe 5 for Plus?
            # Actually, "Multiple accounts" vs "Unlimited accounts" implies a limit. 
            # Let's set Plus to 5 accounts, Pro to None (Unlimited).
            # Re-reading prompt: 
            # - Basic: Single account only
            # - Plus: Multiple accounts
            # - Pro: Unlimited accounts
            # Let's execute with reasoning: "Multiple" usually means > 1 but < infinity. 
            # I will set Plus to 5 for now. I can adjust later if user clarifies.
            # Wait, "Unlimited shared accounts" is in Pro. 
            # Plus has "Shared accounts (invite users)".
            'max_accounts': 5, 
            'max_shared_accounts': 3,
            'pdf_export_limit': 20,
            'can_export_csv': True,
            'has_advanced_analytics': True,
            'has_team_collaboration': False,
            'has_basic_app_features': True,
        }
    )

    SubscriptionPlan.objects.get_or_create(
        name='PRO',
        defaults={
            'price': 19.99,
            'max_accounts': None,  # Unlimited
            'max_shared_accounts': None, # Unlimited
            'pdf_export_limit': 1000, # Effectively unlimited
            'can_export_csv': True,
            'has_advanced_analytics': True,
            'has_team_collaboration': True,
            'has_basic_app_features': True,
        }
    )

    # 2. Assign Basic Plan to Existing Users
    # We iterate all users and create a subscription if they don't have one.
    for user in User.objects.all():
        if not UserSubscription.objects.filter(user=user).exists():
            UserSubscription.objects.create(user=user, plan=basic_plan)

class Migration(migrations.Migration):

    dependencies = [
        ('subscriptions', '0001_initial'),
        ('users', '0001_initial'), # Ensure users table exists
    ]

    operations = [
        migrations.RunPython(create_initial_plans),
    ]
