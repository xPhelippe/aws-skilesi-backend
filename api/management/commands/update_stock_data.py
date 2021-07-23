from api import stock_update_util

from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    help = 'Retrieve stock data for selected stocks (as specified in settings.py) and update stock data in database'

    def handle(self, *args, **options):
        stock_update_util.update_stock_data()
