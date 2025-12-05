from django.db import migrations

def populate_logos(apps, schema_editor):
    """
    DEPRECATED: This migration originally populated CodingStyle logos.
    
    Data seeding has been disabled to allow exclusive management via Django admin.
    All coding style logos should now be set through the admin panel.
    """
    pass  # No-op: Do not seed data via migrations

class Migration(migrations.Migration):

    dependencies = [
        ('myapp', '0121_codingstyle_logo'),
    ]

    operations = [
        migrations.RunPython(populate_logos, reverse_code=migrations.RunPython.noop),
    ]
