"""
Filters for the Transaction model in the application.

This module contains a custom filter set for the Transaction model, allowing users
to filter transactions based on type, date range, and category.
It utilizes the `django_filters` package to create a flexible and user-friendly filtering interface
for transactions in the application.
"""


import django_filters 
from django import forms
from app.models import Transaction, Category


class TransactionFilter(django_filters.FilterSet):
    """
    A filter set for filtering transactions based on various criteria.

    This filter set allows filtering transactions by type, date range, and category.

    Fields:
        transaction_type: Filter transactions by type (e.g., 'Income', 'Expense').
        start_date: Filter transactions that occurred on or after a specific date.
        end_date: Filter transactions that occurred on or before a specific date.
        category: Filter transactions by one or more categories.
    """

    transaction_type = django_filters.ChoiceFilter(
        choices=Transaction.TRANSACTION_TYPE_CHOICES,
        field_name='type',
        lookup_expr='iexact',
        empty_label='Any',  # Label for the empty choice option
    )

    start_date = django_filters.DateFilter(
        field_name="date",
        lookup_expr="gte",  # Greater than or equal to
        label="Date From",  # Display label for the field
        widget=forms.DateInput(attrs={"type": "date"}),  # HTML date input widget
    )

    end_date = django_filters.DateFilter(
        field_name="date",
        lookup_expr="lte",  # Less than or equal to
        label="Date To",  # Display label for the field
        widget=forms.DateInput(attrs={"type": "date"}),  # HTML date input widget
    )

    category = django_filters.ModelMultipleChoiceFilter(
        queryset=Category.objects.all(),
        widget=forms.CheckboxSelectMultiple()  # Use checkboxes for selecting categories
    )


    class Meta:
        model = Transaction
        fields = ('transaction_type',)  # Only include transaction_type in the filter form
