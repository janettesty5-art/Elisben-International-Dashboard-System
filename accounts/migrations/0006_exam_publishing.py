# Create this file: accounts/migrations/0006_exam_publishing.py
# This adds the publishing system fields to the Exam model

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0005_remove_schoolsettings_school_logo'),  # Update to match your last migration
    ]

    operations = [
        # Add is_published field
        migrations.AddField(
            model_name='exam',
            name='is_published',
            field=models.BooleanField(default=False),
        ),
        # Add updated_at field
        migrations.AddField(
            model_name='exam',
            name='updated_at',
            field=models.DateTimeField(auto_now=True),
        ),
    ]