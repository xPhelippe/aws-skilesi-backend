from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver

# Create your models here.


# holds generic infomration about stock
class Stock(models.Model):
    ticker = models.CharField(max_length=10, unique=True)
    description = models.CharField(max_length=3000)
    fullName = models.CharField(max_length=50)

    def __str__(self):
        return self.ticker


# holds time based data about stock


class StockDailyData(models.Model):
    stock = models.ForeignKey(Stock, on_delete=models.CASCADE)
    timestamp = models.DateTimeField(auto_now=False, auto_now_add=False)
    interval = models.CharField(max_length=10)
    open = models.DecimalField(max_digits=7, decimal_places=2)
    high = models.DecimalField(max_digits=7, decimal_places=2)
    low = models.DecimalField(max_digits=7, decimal_places=2)
    close = models.DecimalField(max_digits=7, decimal_places=2)


class StockSMAData(models.Model):
    stock = models.ForeignKey(Stock, on_delete=models.CASCADE)
    timestamp = models.DateTimeField(auto_now=False, auto_now_add=False)
    interval = models.CharField(max_length=10)
    SMA = models.DecimalField(max_digits=7, decimal_places=2)


class StockVWAPData(models.Model):
    stock = models.ForeignKey(Stock, on_delete=models.CASCADE)
    timestamp = models.DateTimeField(auto_now=False, auto_now_add=False)
    interval = models.CharField(max_length=10)
    VWAP = models.DecimalField(max_digits=7, decimal_places=2)


class StockRSIData(models.Model):
    stock = models.ForeignKey(Stock, on_delete=models.CASCADE)
    timestamp = models.DateTimeField(auto_now=False, auto_now_add=False)
    interval = models.CharField(max_length=10)
    RSI = models.DecimalField(max_digits=7, decimal_places=2)


# profile to hold user phone number and their investment type


class Profile(models.Model):
    user = models.OneToOneField(User,
                                on_delete=models.CASCADE,
                                related_name='profile')
    phoneNumber = models.CharField(max_length=12, blank=True)

    investmentType = (
        (0, "LOWRISK"),
        (1, "HIGHRISK"),
    )

    investmentType = models.IntegerField(choices=investmentType, default=0)

    def __str__(self):
        return str(self.user)


# code to update the user profile whenerver the user is editted


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)


@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    instance.profile.save()


class FavStock(models.Model):
    user = models.ForeignKey(User,
                             on_delete=models.CASCADE,
                             related_name='watchlist')
    stock = models.ForeignKey(Stock, on_delete=models.CASCADE)

    def __str__(self):
        return str(self.user) + ', ' + str(self.stock)


class StockOverview(models.Model):

    stock = models.ForeignKey(Stock,
                              on_delete=models.CASCADE,
                              related_name="overview")

    PriceToBookRatio = models.DecimalField(max_digits=7, decimal_places=2)
    PERatio = models.DecimalField(max_digits=7, decimal_places=2)
    PEGRatio = models.DecimalField(max_digits=7, decimal_places=2)
    PriceToSalesRatioTTM = models.DecimalField(max_digits=7, decimal_places=2)
    ShortRatio = models.DecimalField(max_digits=7, decimal_places=2)

    def __str__(self):
        return str(self.stock)
