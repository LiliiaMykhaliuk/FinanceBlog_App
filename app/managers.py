"""
Custom QuerySet for filtering and aggregating transaction data.
"""

from django.db import models


class TransactionQuerySet(models.QuerySet):
    """
    Custom QuerySet for filtering and aggregating transaction data.

    This class provides helper methods to filter transactions based on type
    (expenses or income) and to calculate the total amount of expenses and
    income in USD.
    """

    def get_expenses(self):
        """
        Filters and returns only the transactions of type 'expense'.

        Returns:
            QuerySet: A filtered QuerySet containing 'expense' transactions.
        """

        return self.filter(type='expense')


    def get_income(self):
        """
        Filters and returns only the transactions of type 'income'.

        Returns:
            QuerySet: A filtered QuerySet containing 'income' transactions.
        """

        return self.filter(type='income')


    def get_total_expenses(self):
        """
        Calculates and returns the total sum of all 'expense' transactions in USD.

        Returns:
            float: The total sum of expenses, defaulting to 0 if there are no
                  expenses.
        """

        return self.get_expenses().aggregate(
            total=models.Sum('amount_in_usd')
        )['total'] or 0


    def get_total_income(self):
        """
        Calculates and returns the total sum of all 'income' transactions in USD.

        Returns:
            float: The total sum of income, defaulting to 0 if there are no
                  income transactions.
        """

        return self.get_income().aggregate(
            total=models.Sum('amount_in_usd')
        )['total'] or 0
