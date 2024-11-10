"""
Unit tests for the `Transaction` model's custom queryset methods.

These tests check that the custom methods on the `Transaction` model return correct
results when filtering or aggregating transaction data, specifically income and expense types.

Test Methods:
    - test_queryset_get_income_method: Ensures the `get_income` method only returns 'income' transactions.
    - test_queryset_get_expense_method: Ensures the `get_expenses` method only returns 'expense' transactions.
    - test_queryset_get_total_income_method: Verifies the `get_total_income` method correctly sums income.
    - test_queryset_get_total_expenses_method: Verifies the `get_total_expenses` method correctly sums expenses.

Fixtures:
    - `transactions`: Provides 20 sample `Transaction` instances for testing purposes.

Dependencies:
    - pytest: Testing framework.
    - pytest-django: Provides Django-specific test functionality.
"""


import pytest
from app.models import Transaction

@pytest.mark.django_db
def test_queryset_get_income_method(transactions):
    """
    Test the `get_income` method of the `Transaction` model.
    
    Verifies that the method returns only transactions of type 'income'.
    """

    # Retrieve income transactions using the custom queryset method
    qs = Transaction.objects.get_income()

    # Assert that there are income transactions in the queryset
    assert qs.count() > 0

    # Assert that all transactions returned have type 'income'
    assert all([transaction.type == 'income' for transaction in qs])


@pytest.mark.django_db
def test_queryset_get_expense_method(transactions):
    """
    Test the `get_expenses` method of the `Transaction` model.
    
    Verifies that the method returns only transactions of type 'expense'.
    """

    # Retrieve expense transactions using the custom queryset method
    qs = Transaction.objects.get_expenses()

    # Assert that there are expense transactions in the queryset
    assert qs.count() > 0

    # Assert that all transactions returned has type 'expense'
    assert all([transaction.type == 'expense' for transaction in qs])


@pytest.mark.django_db
def test_queryset_get_total_income_method(transactions):
    """
    Test the `get_total_income` method of the `Transaction` model.
    
    Verifies that the method correctly sums the total income of 'income' transactions.
    """

    # Get total income using the custom queryset method
    total_income = Transaction.objects.get_total_income()

    # Calculate the expected total income by summing the amount_in_usd of all income transactions
    expected_total_income = sum(t.amount_in_usd for t in transactions if t.type == 'income')

    # Assert that the total income from the method matches the expected total income
    assert total_income == expected_total_income


@pytest.mark.django_db
def test_queryset_get_total_expenses_method(transactions):
    """
    Test the `get_total_expenses` method of the `Transaction` model.
    
    Verifies that the method correctly sums the total expenses of 'expense' transactions.
    """

    # Get total expenses using the custom queryset method
    total_expenses = Transaction.objects.get_total_expenses()

    # Calculate the expected total expenses by summing the amount_in_usd of all expense transactions
    expected_total_expenses = sum(t.amount_in_usd for t in transactions if t.type == 'expense')

    # Assert that the total expenses from the method matches the expected total expenses
    assert total_expenses == expected_total_expenses
