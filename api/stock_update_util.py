from time import sleep
from datetime import datetime

from TSIbackend.settings import SELECTED_STOCK_TICKERS, ALPHA_VANTAGE_API_KEY

from api.models import Stock, StockDailyData, StockSMAData, StockVWAPData, \
    StockRSIData, StockOverview

from alpha_vantage.timeseries import TimeSeries
from alpha_vantage.techindicators import TechIndicators
from alpha_vantage.fundamentaldata import FundamentalData

from django.utils import timezone
from django.core.exceptions import ObjectDoesNotExist

import json


def parse_timestamp(timestamp_str):
    try:
        timestamp = timezone.make_aware(
            datetime.strptime(timestamp_str, '%Y-%m-%d'),
            timezone.get_default_timezone())
    except ValueError:
        try:
            timestamp = timezone.make_aware(
                datetime.strptime(timestamp_str, '%Y-%m-%d %H:%M:%S'),
                timezone.get_default_timezone())
        except ValueError:
            timestamp = timezone.make_aware(
                datetime.strptime(timestamp_str, '%Y-%m-%d %H:%M'),
                timezone.get_default_timezone())

    return timestamp


def update_stock_data():
    # Iterate through every stock in settings.py
    for ticker in SELECTED_STOCK_TICKERS:
        # Avoid API limit (5/min)
        print("Waiting 60 seconds to avoid reaching API limit")
        sleep(60)

        print(f"--------Updating stock {ticker}--------")
        stock = update_stock_overview(ticker)
        update_stock_daily_data(stock)
        update_sma_data(stock)
        update_vwap_data(stock)
        update_rsi_data(stock)
        print("")

    print("Done updating stock data")


def update_stock_overview(ticker):
    fd = FundamentalData(key=ALPHA_VANTAGE_API_KEY,
                         output_format='json',
                         indexing_type='date')

    print("Getting company overview")
    company_data, metadata = fd.get_company_overview(ticker)

    print("Updating company overview")
    try:
        stock = Stock.objects.get(ticker=ticker)
        print("Stock already in database. Not adding.")
    except ObjectDoesNotExist:
        print("Adding stock to database")
        stock = Stock()
        stock.ticker = ticker

    stock.description = company_data['Description'][:3000]
    stock.fullName = company_data['Name'][:50]
    stock.save()

    try:
        stockOverview = StockOverview.objects.get(stock=stock)
        print("Overview already in database. Not adding")
    except:
        print("Adding overview to database")
        stockOverview = StockOverview()
        stockOverview.stock = stock

    stockOverview.PEGRatio = company_data['PEGRatio']
    stockOverview.PriceToBookRatio = company_data['PriceToBookRatio']
    stockOverview.PERatio = company_data['PERatio']
    stockOverview.PriceToSalesRatioTTM = company_data['PriceToSalesRatioTTM']
    stockOverview.ShortRatio = company_data['ShortRatio']
    stockOverview.save()

    return stock


def update_stock_daily_data(stock):
    ts = TimeSeries(key=ALPHA_VANTAGE_API_KEY,
                    output_format='json',
                    indexing_type='date')

    print("Getting ticker daily adjusted")
    daily_data, metadata = ts.get_daily_adjusted(symbol=stock.ticker,
                                                 outputsize='compact')

    try:
        latest_data = StockDailyData.objects.filter(
            stock=stock).latest('timestamp')
        print("Existing daily adjusted data found in database")
        latest_timestamp = latest_data.timestamp
    except ObjectDoesNotExist:
        latest_timestamp = None
        print("No daily adjusted data found in database")

    print(f"Updating stock daily data ({len(daily_data)} entries to process)")
    daily_data_set = []
    for day in daily_data:
        # Don't add existing data
        timestamp = parse_timestamp(day)
        if latest_timestamp != None and timestamp < latest_timestamp:
            continue

        db_daily_data = StockDailyData()
        db_daily_data.stock = stock
        db_daily_data.timestamp = timestamp
        db_daily_data.interval = 'daily'
        db_daily_data.open = daily_data[day]['1. open']
        db_daily_data.high = daily_data[day]['2. high']
        db_daily_data.low = daily_data[day]['3. low']
        db_daily_data.close = daily_data[day]['4. close']
        db_daily_data.save()

        daily_data_set.append(db_daily_data)

    return daily_data_set


def update_sma_data(stock):
    ti = TechIndicators(key=ALPHA_VANTAGE_API_KEY,
                        output_format='json',
                        indexing_type='date')

    print("Getting SMA data")
    sma_data, metadata = ti.get_sma(symbol=stock.ticker,
                                    interval='daily',
                                    series_type='compact')

    try:
        latest_data = StockSMAData.objects.filter(
            stock=stock).latest('timestamp')
        print("Existing SMA data found in database")
        latest_timestamp = latest_data.timestamp
    except ObjectDoesNotExist:
        latest_timestamp = None
        print("No SMA data found in database")

    print(f"Updating stock SMA data ({len(sma_data)} entries to process)")
    sma_data_set = []
    for time in sma_data:
        timestamp = parse_timestamp(time)

        # Don't add existing data
        if latest_timestamp != None and timestamp < latest_timestamp:
            continue

        db_sma_data = StockSMAData()
        db_sma_data.stock = stock
        db_sma_data.timestamp = timestamp
        db_sma_data.SMA = sma_data[time]['SMA']
        db_sma_data.save()

        sma_data_set.append(db_sma_data)

    return sma_data_set


def update_vwap_data(stock):
    ti = TechIndicators(key=ALPHA_VANTAGE_API_KEY,
                        output_format='json',
                        indexing_type='date')

    print("Getting VWAP data")
    vwap_data, metadata = ti.get_vwap(symbol=stock.ticker, interval='5min')

    try:
        latest_data = StockVWAPData.objects.filter(
            stock=stock).latest('timestamp')
        print("Existing VWAP data found in database")
        latest_timestamp = latest_data.timestamp
    except ObjectDoesNotExist:
        latest_timestamp = None
        print("No VWAP data found in database")

    print(f"Updating stock VWAP data ({len(vwap_data)} entries to process)")
    vwap_data_set = []
    for time in vwap_data:
        timestamp = parse_timestamp(time)
        # Don't add existing data
        if latest_timestamp != None and timestamp < latest_timestamp:
            continue

        db_vwap_data = StockVWAPData()
        db_vwap_data.stock = stock
        db_vwap_data.timestamp = timestamp
        db_vwap_data.VWAP = vwap_data[time]['VWAP']
        db_vwap_data.save()

        vwap_data_set.append(db_vwap_data)

    return vwap_data_set


def update_rsi_data(stock):
    ti = TechIndicators(key=ALPHA_VANTAGE_API_KEY,
                        output_format='json',
                        indexing_type='date')

    print("Getting RSI data")
    rsi_data, metadata = ti.get_rsi(symbol=stock.ticker,
                                    interval='daily',
                                    series_type='close')

    try:
        latest_data = StockRSIData.objects.filter(
            stock=stock).latest('timestamp')
        print("Existing RSI data found in database")
        latest_timestamp = latest_data.timestamp
    except ObjectDoesNotExist:
        latest_timestamp = None
        print("No RSI data found in database")

    print(f"Updating stock RSI data ({len(rsi_data)} entries to process)")
    rsi_data_set = []
    for time in rsi_data:
        timestamp = parse_timestamp(time)
        # Don't add existing data
        if latest_timestamp != None and timestamp < latest_timestamp:
            continue

        db_rsi_data = StockRSIData()
        db_rsi_data.stock = stock
        db_rsi_data.timestamp = timestamp
        db_rsi_data.RSI = rsi_data[time]['RSI']
        db_rsi_data.save()

        rsi_data_set.append(db_rsi_data)

    return rsi_data_set
