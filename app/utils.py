"""
Module to handle fetching and converting exchange rates for different currencies.

This module provides functions to fetch exchange rates from an external API,
cache them to improve performance, and convert an amount from any currency to EUR
based on the latest rates. It uses Django's caching mechanism to avoid making
repeated API calls and to store the rates for efficient access.
"""


import os
from decimal import Decimal

import requests

from django.conf import settings
from django.core.cache import cache



def fetch_exchange_rates():
    """
    Fetches the latest exchange rates via an API call.

    Returns:
        dict or None: A dictionary of conversion rates or None if the request fails.
    """

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
    """
    Retrieves the exchange rate for a specific target currency from the cache
    or makes an API call to fetch the rates.

    If the exchange rates are not found in the cache, it fetches them using
    `fetch_exchange_rates()` and caches the result.

    Args:
        target_currency (str): The currency for which to fetch the exchange rate.

    Returns:
        float: The exchange rate for the target currency, or None if not available.
    """

    # Try to get the exchange rates from the cache
    exchange_rates = cache.get('conversion_rates')

    # If the exchange rates are not in the cache, fetch them from the API and store them in the cache
    if not exchange_rates:
        exchange_rates = fetch_exchange_rates()

        if not exchange_rates:
            # # If the API call fails, return a default value of 1 (EUR as base currency)
            return 1

        # Cache the exchange rates for 1 hour
        cache.set('conversion_rates', exchange_rates, timeout=3600)

    return exchange_rates.get(target_currency, None) # Return None if target_currency is not found


def get_exchange_rates():
    """
    Retrieves the latest exchange rates from the cache or makes an API call to fetch them.

    If the exchange rates are not in the cache, it fetches them using `fetch_exchange_rates()`
    and caches the result.

    Returns:
        dict or None: A dictionary of conversion rates or None if fetching fails.
    """

    # Try to get the exchange rates from the cache
    exchange_rates = cache.get('conversion_rates')

    # If the exchange rates are not in the cache, fetch them from the API and store them in the cache
    if not exchange_rates:
        exchange_rates = fetch_exchange_rates()

        if not exchange_rates:
            # # If the API call fails, return None
            return None

        # Cache the exchange rates for 1 hour
        cache.set('conversion_rates', exchange_rates, timeout=3600)

    return exchange_rates


def convert_to_EUR(amount, currency):
    """
    Converts a given amount to EUR based on the exchange rate.

    Args:
        amount (float): The amount to convert.
        currency (str): The currency code of the given amount.

    Returns:
        float: The amount converted to EUR, or 0 if the exchange rate is unavailable.
    """

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
