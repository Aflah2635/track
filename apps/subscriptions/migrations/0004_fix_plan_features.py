from django.db import migrations

def fix_plan_features(apps, schema_editor):
    SubscriptionPlan = apps.get_model('subscriptions', 'SubscriptionPlan')
    
    # Update Plus Plan
    SubscriptionPlan.objects.filter(name='PLUS').update(
        allow_export=True,
        allow_advanced_analytics=True,
        max_shared_accounts=3, # As per Step 1 prompt
    )
    
    # Update Pro Plan
    SubscriptionPlan.objects.filter(name='PRO').update(
        allow_export=True,
        allow_advanced_analytics=True,
        has_team_collaboration=True,
        max_shared_accounts=None, # Unlimited
        pdf_export_limit=None, # Unlimited
    )
    
    # Ensure Basic Plan is strict
    SubscriptionPlan.objects.filter(name='BASIC').update(
        allow_export=False,
        allow_advanced_analytics=False,
        has_team_collaboration=False,
        max_shared_accounts=0,
        pdf_export_limit=5,
    )

class Migration(migrations.Migration):

    dependencies = [
        ('subscriptions', '0003_rename_has_advanced_analytics_subscriptionplan_allow_advanced_analytics_and_more'),
    ]

    operations = [
        migrations.RunPython(fix_plan_features),
    ]
