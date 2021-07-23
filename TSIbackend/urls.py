"""TSIbackend URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import include, path
from api import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('login/', views.login_user),
    path('update_stock_data/',
         views.update_stock_data,
         name='update_stock_data'),
    path('add_to_watchlist/', views.add_to_watchlist, name='add_to_watchlist'),
    path('change_user_info/', views.change_user_info, name='change_user_info'),
    path('remove_from_watchlist/',
         views.remove_from_watchlist,
         name='chage_user_info'),
    path('create_user/', views.create_user, name='create_user'),
    path('stocks/daily_adjusted/<str:ticker>',
         views.get_daily_adjusted,
         name='get_daily_adjusted'),
    path('stocks/SMA/<str:ticker>', views.get_sma, name='get_sma'),
    path('stocks/VWAP/<str:ticker>', views.get_vwap, name='get_vwap'),
    path('stocks/RSI/<str:ticker>', views.get_rsi, name='get_rsi'),
    path('get_all_tickers', views.get_all_tickers, name='get_all_tickers'),
    path('get_stock_overview/',
         views.get_stock_overview,
         name='get_stock_overview')
]
