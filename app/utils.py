import os
import requests
from django.conf import settings
from django.core.cache import cache
from decimal import Decimal


def fetch_exchange_rates():
    '''Functions makes an API call and fetches up to date exchange rates'''

    full_url = f"{settings.API_URL}{settings.API_KEY}{settings.API_ENDPOINT}"

    # API call to fetch exchange rates
    try:
        response = requests.get(full_url)
        response.raise_for_status() # Raise an exception if the request was unsuccessful
        data = response.json()
        return data['conversion_rates']
    except requests.RequestException as error:
        print(f'Error in API call: {error}')
        return None

def get_exchange_rate_for_target_currency(target_currency):
    '''Function to get exchange rates from cache or make an API call'''

    # Try to get the exchange rates from the cache
    exchange_rates = cache.get('conversion_rates')

    # If the exchange rates are not in the cache, fetch them from the API and store them in the cache
    if not exchange_rates:
        exchange_rates = fetch_exchange_rates()

        if not exchange_rates:
            # # If the API call fails, return a default value of 1 (USD as base currency)
            return 1

        # Cache the exchange rates for 1 hour
        cache.set('conversion_rates', exchange_rates, timeout=3600)

    return exchange_rates.get(target_currency, None) # Return 1 for USD as a default currency


def get_exchange_rates():
    '''Function to get exchange rates from cache or make an API call'''

    # Try to get the exchange rates from the cache
    exchange_rates = cache.get('conversion_rates')

    # If the exchange rates are not in the cache, fetch them from the API and store them in the cache
    if not exchange_rates:
        exchange_rates = fetch_exchange_rates()

        if not exchange_rates:
            # # If the API call fails, return a default value of 1 (USD as base currency)
            return None

        # Cache the exchange rates for 1 hour
        cache.set('conversion_rates', exchange_rates, timeout=3600)

    return exchange_rates


def convert_to_EUR(amount, currency):
    '''Function to convert an amount to EUR based on the exchange rate'''

    # Get exchange rate for target currency
    exchange_rate = get_exchange_rate_for_target_currency(currency)

    if exchange_rate:
        # Convert exchange_rate to Decimal before performing the division
        exchange_rate_decimal = Decimal(str(exchange_rate))
        # Convert amount to EUR and round to 2 decimal places
        amount_in_usd = round(amount / exchange_rate_decimal, 2)
    else:
        # If the exchange rate is not available, return the original amount
        amount_in_usd = 0

    return amount_in_usd
