from django.core.management.base import BaseCommand

### CRONTAB ###
# 0 0 1 1 * cd /home/ecole01/intranet && python manage.py auto_test > /home/ecole01/logs/cron.log
def cron_test():
    print("Je test le cron tab")

class Command(BaseCommand):
    def handle(self, **options):
        cron_test()