"""
Factories for generating test data for the User, Category, and Transaction models.

This module uses the `factory_boy` package to define factories for the models in the app,
which will help generate mock data for testing purposes.
"""


from datetime import datetime
import factory 
from app.models import Category, Transaction, User


class UserFactory(factory.django.DjangoModelFactory):
    """
    Factory class for creating instances of the User model for testing purposes.
    Ensures that each User has a unique username.
    """

    class Meta:
        model = User  # The model this factory creates instances of.
        django_get_or_create = ('username',)  # Ensure unique usernames during creation

    first_name = factory.Faker('first_name')
    last_name = factory.Faker('last_name')
    username = factory.Sequence(lambda n: 'user%d' % n)  # Generate unique usernames



class CategoryFactory(factory.django.DjangoModelFactory):
    """
    Factory for creating instances of the Category model for testing purposes.

    This factory ensures each category has a unique name from a predefined list.
    """

    class Meta:
        model = Category  # The model this factory creates instances of.
        django_get_or_create = ('name',)  # Ensures unique category names

    name = factory.Iterator(
        ['Bills', 'Rent', 'Salary', 'Food', 'Subscriptions']  # Predefined category names
    )



class TransactionFactory(factory.django.DjangoModelFactory):
    """
    Factory for creating instances of the Transaction model for testing purposes.

    This factory generates transactions with random data and links them to a user and category.
    """

    class Meta:
        model = Transaction  # The model this factory creates instances of.

    user = factory.SubFactory(UserFactory)  # Link to a randomly generated user
    category = factory.SubFactory(CategoryFactory)  # Link to a randomly generated category
    amount = 5  # Default transaction amount
    currency = 'USD'  # Default currency
    amount_in_usd = 5  # Default USD amount
    date = factory.Faker(
        'date_between',
        start_date=datetime(year=2022, month=1, day=1).date(),
        end_date=datetime.now().date() # Random date of transaction between Jan 1, 2022, and today
    )
    type = factory.Iterator(
        [
            x[0] for x in Transaction.TRANSACTION_TYPE_CHOICES  # Random transaction type
        ]
    )
