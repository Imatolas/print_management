from django.db import migrations, models
import datetime

class Migration(migrations.Migration):

    dependencies = [
        ('core', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='component',
            name='material',
            field=models.CharField(verbose_name='Material', max_length=60, blank=True),
        ),
        migrations.AddField(
            model_name='component',
            name='production_time',
            field=models.DurationField(verbose_name='Tempo de produção', default=datetime.timedelta()),
        ),
    ]
