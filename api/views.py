from api import stock_update_util

from django.http import HttpResponse, JsonResponse
from django.shortcuts import render
from django.views.decorators.http import require_http_methods, require_GET, require_POST
from django.contrib.auth.models import User
from django.views.decorators.csrf import csrf_exempt
from api.models import Stock, StockDailyData, StockSMAData, StockVWAPData, \
    StockRSIData
from .serializers import UserSerializer, ProfileSerializer, WatchListSerializer

from .models import Profile, Stock, FavStock, StockOverview
import json

from django.core.exceptions import ObjectDoesNotExist


def getUserDataJson(user):
    userSerial = UserSerializer(user)

    profile = Profile.objects.get(user=user)

    retData = dict()
    retData.update(userSerial.data)
    retData.update({"investmentType": profile.investmentType})

    return retData


# Create a user
# inputs:
# - username [required]
# - password [required]
# - first_name  [required]
# - last_name [required]
# - email [optional]
# - phonenumber [optional]
# - risk_type [optional]
# outputs:
# - status message
# - user object of information
@csrf_exempt
@require_http_methods(['POST', 'OPTIONS'])
def create_user(request):

    # grabbing relevant infromation from post
    username = request.POST.get('username')
    password = request.POST.get('password')
    first_name = request.POST.get('first_name')
    last_name = request.POST.get('last_name')
    email = request.POST.get('email')
    phonenumber = request.POST.get('phonenumber')
    risk_type = request.POST.get('risk_type')

    print("user information received")

    # set empty values if fields are empty
    if not email:
        email = " "

    # checking for required fields
    missing = []

    if not first_name:
        missing.append("first_name")

    if not last_name:
        missing.append("last_name")

    if not username:
        missing.append("username")

    if not password:
        missing.append("password")

    if len(missing) > 0:
        resp = {"status": "missing required information", "missing": missing}

        return JsonResponse(resp, status=404)

    # see if user already exists
    try:
        user = User.objects.get(username=username)

        resp = {"status": "User already exists"}

        return JsonResponse(resp, status=404)
    except ObjectDoesNotExist:
        # create user
        user = User(
            username=username,
            first_name=first_name,
            last_name=last_name,
            email=email,
        )
        user.set_password(password)
        user.save()

        user.profile.phoneNumber = phonenumber
        user.profile.risk_type = risk_type

        # add TSLA to their watchlist by default
        stock = Stock.objects.get(ticker="TSLA")
        FavStock.objects.create(user=user, stock=stock)

        # create serialzed user information
        userSerial = UserSerializer(user)

        profile = Profile.objects.get(user=user)

        retData = dict()
        retData.update(userSerial.data)
        retData.update({"investmentType": profile.investmentType})

        resp = {
            "status": "user " + user.username + " successfully created",
            "userData": retData
        }

        return JsonResponse(resp, status=200)
    except Exception:

        resp = {"status": "Error Occured"}
        print(str(Exception))

        return JsonResponse(resp, status=500)


# modifying a user's data
# inputs:
# - username [required]
# - first_name [optional]
# - last_name  [optional]
# - risk_type [optional]
# - email [optional]
# - Phone number [optional]
# outputs:
# - success message
# - new user information
@csrf_exempt
@require_http_methods(['POST', 'OPTIONS'])
def change_user_info(request):

    # get username from post request
    username = request.POST.get('username')

    # response dictionary
    resp = dict()

    resp.update({"status": ""})

    # grab the relevant information from the database
    try:
        user = User.objects.get(username=username)
        resp['status'] = "user updated successfully"
    except ObjectDoesNotExist:
        resp["status"] = "User does not exist"
        return JsonResponse(resp, status=404)
    except Exception:

        resp = {"status": "Error Occured"}
        print(str(Exception))

        return JsonResponse(resp, status_code=500)

    userchanges = dict()

    # modify first_name
    first_name = request.POST.get('first_name')
    if first_name:

        user.first_name = first_name

        userchanges.update({"first_name": first_name})

    # modify last_name
    last_name = request.POST.get('last_name')
    if last_name:

        user.last_name = last_name

        userchanges.update({"last_name": last_name})

    # modify phonenumber
    phonenumber = request.POST.get('phonenumber')
    if phonenumber:

        user.profile.phoneNumber = phonenumber

        userchanges.update({"phonenumber": phonenumber})

    # modify email
    email = request.POST.get('email')
    if email:

        user.email = email

        userchanges.update({"email": email})

    # modify risk type
    investment_type = request.POST.get('investment_type')
    if investment_type:

        user.profile.investmentType = investment_type

        userchanges.update({"investment_type": investment_type})

    resp.update({"changes": userchanges})

    user.save()

    return JsonResponse(resp, status=200)


# removing a stock from the user's watchlist
# inputs:
# - username
# - ticker
# output:
# - status message
@csrf_exempt
@require_http_methods(['POST', 'OPTIONS'])
def remove_from_watchlist(request):
    # grab info from request
    username = request.POST.get("username")
    ticker = request.POST.get("ticker")

    # grab the relevant information from the database
    try:
        user = User.objects.get(username=username)
    except:
        res = {"status": "User does not exist"}

        return JsonResponse(res)

    try:
        stock = Stock.objects.get(ticker=ticker)
    except:
        res = {"status": "Invalid ticker"}

        return JsonResponse(res)

    favStock = FavStock.objects.filter(user=user, stock=stock)

    if favStock:
        favStock.delete()

        userJson = getUserDataJson(user)

        res = {
            "status": ticker + " was removed from " + username + "'s watchlist",
            "userData": userJson
        }

        return JsonResponse(res, status=200)
    else:
        res = {"status": ticker + " is not on " + username + "'s watchlist"}

        return JsonResponse(res, status=404)


# adding a stock to the user's watchlist
# inputs:
# - username
# - ticker
# outputs:
# - success message
@csrf_exempt
@require_http_methods(['POST', 'OPTIONS'])
def add_to_watchlist(request):

    # grab info from request
    username = request.POST.get("username")
    ticker = request.POST.get("ticker")

    # grab the relevant information from the database
    try:
        user = User.objects.get(username=username)
    except ObjectDoesNotExist:
        res = {"status": "User does not exist"}

        return JsonResponse(res, status=404)
    except Exception:

        resp = {"status": "Error Occured"}
        print(str(Exception))

        return JsonResponse(resp, status_code=404)

    try:
        stock = Stock.objects.get(ticker=ticker)
    except ObjectDoesNotExist:
        res = {"status": "Invalid ticker"}

        return JsonResponse(res, status=404)
    except Exception:

        resp = {"status": "Error Occured"}
        print(str(Exception))

        return JsonResponse(resp, status=500)

    favStock = FavStock.objects.filter(user=user, stock=stock)

    if len(favStock) == 0:

        # add stock to watchlist
        FavStock.objects.create(user=user, stock=stock)

        # construct array of current watch list
        retStocks = []
        favstock_set = FavStock.objects.filter(user=user)
        for item in favstock_set:
            retStocks.append(str(item.stock))

        # grab the user's data
        userJson = getUserDataJson(user)

        # create return object
        res = {"status": "success", "userData": userJson}
        return JsonResponse(res, status=200)
    else:

        res = {"status": "User already has this on their watchlist"}

        return JsonResponse(res, status=404)


# Logging in the user
# POST request inputs:
# - username
# - password
# return:
# - username
# - first_name
# - last_name
# - watchlist
# - risk type


@csrf_exempt
@require_http_methods(['POST', 'OPTIONS'])
def login_user(request):

    # get the username of the user
    username = request.POST.get("username")
    password = request.POST.get("password")

    print(request.POST)

    # try to get the user
    try:
        user = User.objects.get(username=username)
    except:

        resp = {"status": "User does not exist"}
        return JsonResponse(resp, status=404)

    print("got the correct user")
    # see if the password is correct
    if user.check_password(password):

        print("password checks out")
        # serialize user profile
        userSerial = UserSerializer(user)

        profile = Profile.objects.get(user=user)

        retData = dict()
        retData.update(userSerial.data)
        retData.update({"investmentType": profile.investmentType})

        # grab user information and send over
        return JsonResponse(retData)
    else:

        resp = {"status": "password is not valid"}
        return JsonResponse(resp, status=404)


def update_stock_data(request):
    stock_update_util.update_stock_data()

    return JsonResponse({"status": "Done updating stock data"})


"""
    Decorator for getting stock data. All currently-supported stock data follows
    similar format.
    Endpoint URI must end with /<ticker>.
    Parameters:
      * stock_data_model: Stock data model
      * data_type_name: Name of stock data type
      * values: List of values to retrieve from model and return in response
    Query Params:
      * start_time: oldest timestamp of data to retrieve
      * end_time: newest timestamp of data to retrieve
    Response (JSON):
    {
      "<data_type_name>": [
        {
          "timestamp": timestamp of data point,
          *values: *value data
        }
      ]
    }
"""


def stock_data_get(stock_data_model, data_type_name, values):

    def decorator(func):

        @require_GET
        def inner(request, ticker):
            # Get start_time and end_time query paramaters
            start_time = request.GET.get('start_time')
            end_time = request.GET.get('end_time')

            # Ensure start_time and end_time were specified
            if start_time == None:
                resp = {'status': 'Please specify start_time'}
                return JsonResponse(resp, status=400)
            elif end_time == None:
                resp = {'status': 'Please specify end_time'}
                return JsonResponse(resp, status=400)

            # Find stock with given ticker
            try:
                stock = Stock.objects.get(ticker=ticker)
            except ObjectDoesNotExist:
                resp = {'status': f"Stock with ticker {ticker} does not exist"}
                return JsonResponse(resp, status=400)
            except Exception:
                resp = {"status": "Error Occured"}
                print(str(exception))

                return JsonResponse(resp, status_code=500)

            # Get QuerySet of data between start_time and end_time
            data_filter = stock_data_model.objects.filter(
                stock=stock, timestamp__gte=start_time, timestamp__lte=end_time)
            # Get values from QuerySet
            data = data_filter.values('timestamp', *values)
            # Create JSON response of values
            resp = {data_type_name: list(data)}

            return JsonResponse(resp)

        return inner

    return decorator


"""
    Get daily adjusted data for a particular stock
    Endpoint: /stocks/daily_adjusted/<str:ticker>
    Query Params:
      * start_time: oldest timestamp of data to retrieve
      * end_time: newest timestamp of data to retrieve
    Response (JSON):
    {
      "daily_adjusted": [
        {
          "timestamp": timestamp of data point,
          "interval": interval of data points,
          "open": value of stock at open,
          "high": highest value of stock,
          "low": lowest value of stock,
          "close": value of stock at close
        }
      ]
    }
"""


@stock_data_get(StockDailyData, 'daily_adjusted',
                ['interval', 'open', 'high', 'low', 'close'])
def get_daily_adjusted(request, ticker):
    pass


"""
    Get SMA data for a particular stock
    Endpoint: /stocks/SMA/<str:ticker>
    Query Params:
      * start_time: oldest timestamp of data to retrieve
      * end_time: newest timestamp of data to retrieve
    Response (JSON):
    {
      "SMA": [
        {
          "timestamp": timestamp of data point,
          "SMA": SMA at timestamp
        }
      ]
    }
"""


@stock_data_get(StockSMAData, 'SMA', ['SMA'])
def get_sma(request, ticker):
    pass


"""
    Get VWAP data for a particular stock
    Endpoint: /stocks/VWAP/<str:ticker>
    Query Params:
      * start_time: oldest timestamp of data to retrieve
      * end_time: newest timestamp of data to retrieve
    Response (JSON):
    {
      "VWAP": [
        {
          "timestamp": timestamp of data point,
          "VWAP": VWAP at timestamp
        }
      ]
    }
"""


@stock_data_get(StockVWAPData, 'VWAP', ['VWAP'])
def get_vwap(request, ticker):
    pass


"""
    Get RSI data for a particular stock
    Endpoint: /stocks/RSI/<str:ticker>
    Query Params:
      * start_time: oldest timestamp of data to retrieve
      * end_time: newest timestamp of data to retrieve
    Response (JSON):
    {
      "RSI": [
        {
          "timestamp": timestamp of data point,
          "RSI": RSI at timestamp
        }
      ]
    }
"""


@stock_data_get(StockRSIData, 'RSI', ['RSI'])
def get_rsi(request, ticker):
    pass


""" 
    Get all tickers stored in the database
    Endpoint: /get_all_tickers
    Params: None

    Response (JSON):
    {
        "tickers": [ array of tickers ]
    }

"""


@require_GET
def get_all_tickers(request):
    # grab all stock tickers
    tickers = Stock.objects.all().values('ticker').distinct()

    ret = []

    for tickerObject in tickers:
        ret.append(tickerObject['ticker'])

    retData = {"tickers": ret}

    return JsonResponse(retData, status=200)


"""
    Get the overview indicators for a specific stock
    Endpoint: /get_stock_overview

    Post Body Params:
    * ticker: ticker of the desired stock

    Response (JSON):
    {
        "ticker": stock ticker
        "PriceToBookRatio": PriceToBookRatio of the stock,
        "PERatio": PERatio of the stock,
        "PEGRatio": PEGRatio of the stock,
        "PriceToSalesRatioTTM": PriceToSalesRatioTTM of the stock,
        "ShortRatio":ShortRatio of the stock
    }
"""


@csrf_exempt
@require_POST
def get_stock_overview(request):
    # get ticker
    try:
        ticker = request.POST["ticker"]
    except ObjectDoesNotExist:
        resp = {"status": ticker + " Does not exist"}

        return JsonResponse(resp, status=404)

    try:
        stock = Stock.objects.get(ticker=ticker)
    except ObjectDoesNotExist:
        resp = {"status": ticker + " is not a valid stock"}

        return JsonResponse(resp, status=404)

    stock_overview = StockOverview.objects.get(stock=stock)

    resp = {
        "ticker": str(stock_overview.stock),
        "PriceToBookRatio": stock_overview.PriceToBookRatio,
        "PERatio": stock_overview.PERatio,
        "PEGRatio": stock_overview.PEGRatio,
        "PriceToSalesRatioTTM": stock_overview.PriceToSalesRatioTTM,
        "ShortRatio": stock_overview.ShortRatio,
    }

    return JsonResponse(resp, status=200)
