"""
This file contains shared test fixtures for the project, which are automatically
discovered by pytest and made available across the test suite.

Fixtures in this file provide reusable data setups for testing, including:
    - Bulk creation of transactions with random data.
    - User-specific transaction setups for testing user-associated functionality.
    - A dictionary of transaction parameters for testing functions or views that
      require transaction details
"""


import pytest
from app.factories import TransactionFactory, UserFactory

@pytest.fixture
def transactions():
    """
    Fixture to create a batch of 20 transactions with random data.
    """
    return TransactionFactory.create_batch(20)


@pytest.fixture
def user_transactions():
    """
    Fixture to create a new user and associate 20 transactions with that user.
    """
    user = UserFactory()
    return TransactionFactory.create_batch(20, user=user)


@pytest.fixture
def user():
    """
    Fixture to create a single user.
    """
    return UserFactory()


@pytest.fixture
def transaction_dict_params(user):
    """
    Fixture to create a transaction dictionary with specified parameters for a given user.
    
    Args:
        user: The user associated with the transaction.

    Returns:
        dict: A dictionary of transaction parameters that includes the type, category, date, amount,
              currency, and converted amount in USD.
    """

    transaction = TransactionFactory.create(user=user)
    return {
        'type': transaction.type,
        'category': transaction.category_id,
        'date': transaction.date,
        'amount': transaction.amount,
        'currency': transaction.currency,
        'amount_in_usd': transaction.amount_in_usd,
    }


