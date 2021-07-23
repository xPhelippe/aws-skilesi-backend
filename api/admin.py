from django.contrib import admin
from .models import *

# Register your models here.

admin.site.register(Stock)
admin.site.register(Profile)
admin.site.register(StockDailyData)
admin.site.register(StockRSIData)
admin.site.register(StockSMAData)
admin.site.register(StockVWAPData)
admin.site.register(FavStock)
admin.site.register(StockOverview)
