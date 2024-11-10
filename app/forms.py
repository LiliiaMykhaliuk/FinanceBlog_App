"""
Forms module for the application. Contains forms related to user registration,
subscribing, commenting, and submitting transactions. Each form provides 
validation and custom widgets for handling user inputs.

Classes:
    - CommentForm: A form for submitting comments.
    - SubscribeForm: A form for subscribing with an email address.
    - NewUserForm: A form for user registration, extending Django's UserCreationForm.
    - TransactionForm: A form for submitting financial transactions.
"""


# Standard library imports
from django import forms

# Third-party imports
from django.utils.translation import gettext_lazy as _
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User

# Local imports
from app.models import Comments, Subscribe, Transaction, Category


class CommentForm(forms.ModelForm):
    """
    A form for creating and submitting comments.

    Fields:
        content: The content of the comment.
        email: The email address of the commenter.
        name: The name of the commenter.
        website: The website URL of the commenter (optional).
    """

    class Meta:
        model = Comments
        fields = {'content', 'email', 'name', 'website'}

    def __init__(self, *args, **kwargs):
        """
        Initialize the form with custom placeholder text for each field.
        """

        super().__init__(*args, **kwargs)
        self.fields['content'].widget.attrs['placeholder'] = 'Type your comment...'
        self.fields['email'].widget.attrs['placeholder'] = 'Email'
        self.fields['name'].widget.attrs['placeholder'] = 'Name'
        self.fields['website'].widget.attrs['placeholder'] = 'Website'


class SubscribeForm(forms.ModelForm):
    """
    A form for subscribing to the blog with an email address.

    Fields:
        email: The email address to subscribe.
    """

    class Meta:
        model = Subscribe
        fields = '__all__'
        labels = {'email':_('')}

    
    def __init__(self, *args, **kwargs):
        """
        Initialize the form with a placeholder for the email field.
        """

        super().__init__(*args, **kwargs)
        self.fields['email'].widget.attrs['placeholder'] = 'Enter your email'


class NewUserForm(UserCreationForm):
    """
    A form for user registration, extending Django's UserCreationForm.

    Fields:
        username: The username for the new user.
        email: The email address of the new user.
        password1: The password for the new user.
        password2: A confirmation of the password.
    """

    class Meta:
        model = User
        fields = ("username", "email", "password1", "password2")

    def __init__(self, *args, **kwargs):
        """
        Initialize the form with custom placeholder text for each field.
        """

        super().__init__(*args, **kwargs)
        self.fields['username'].widget.attrs['placeholder'] = 'Username'
        self.fields['email'].widget.attrs['placeholder'] = 'Email'
        self.fields['password1'].widget.attrs['placeholder'] = 'Password'
        self.fields['password2'].widget.attrs['placeholder'] = 'Repeat password'

    def clean_username(self):
        """
        Ensure the username is unique by checking if it already exists in the database.

        Returns:
            str: The cleaned username.

        Raises:
            forms.ValidationError: If the username already exists.
        """

        username = self.cleaned_data['username'].lower()  
        new = User.objects.filter(username = username)
        if new.count():
            raise forms.ValidationError("User Already Exist")
        return username

    def clean_email(self):
        """
        Ensure the email is unique by checking if it already exists in the database.

        Returns:
            str: The cleaned email.

        Raises:
            forms.ValidationError: If the email already exists.
        """

        email = self.cleaned_data['email'].lower()  
        new = User.objects.filter(email = email)
        if new.count():
            raise forms.ValidationError("Email Already Exist")
        return email

    def clean_password2(self):
        """
        Ensure both passwords match.

        Returns:
            str: The cleaned second password.

        Raises:
            forms.ValidationError: If the passwords do not match.
        """

        password1 = self.cleaned_data['password1']
        password2 = self.cleaned_data['password2']

        if password1 and password2 and password1 != password2:
            raise forms.ValidationError("Passwords don't match")
        return password2


# Define a default list of currencies
DEFAULT_CURRENCIES = [
    ('USD', 'US Dollar'),
    ('EUR', 'Euro'),
    ('GBP', 'British Pound'),
    ('JPY', 'Japanese Yen'),
    ('AUD', 'Australian Dollar'),
    ('CAD', 'Canadian Dollar'),
    ('CHF', 'Swiss Franc'),
    ('CNY', 'Chinese Yuan'),
    ('INR', 'Indian Rupee'),
    ]


class TransactionForm(forms.ModelForm):
    """
    A form for creating and submitting a transaction.

    Fields:
        type: The type of the transaction (income, expense).
        amount: The amount of money involved in the transaction.
        currency: The currency in which the transaction is made.
        date: The date the transaction occurred.
        category: The category to which the transaction belongs (e.g., bills, food).
    """

    category = forms.ModelChoiceField(
        queryset=Category.objects.all(),
        widget=forms.RadioSelect()
    )

    # Empty by default, populated in the view
    currency = forms.ChoiceField(choices=DEFAULT_CURRENCIES, required=True)

    def __init__(self, *args, currencies=None, **kwargs):
        """
        Initialize the form with dynamic currency choices if provided,
        otherwise use the default list of currencies.
        """

        super(TransactionForm, self).__init__(*args, **kwargs)
        if currencies:
            # If dynamic currencies are passed, override default choices
            self.fields['currency'].choices = currencies
        else:
            # Fallback to default currencies
            self.fields['currency'].choices = DEFAULT_CURRENCIES

    def clean_amount(self):
        """
        Ensure that the amount is a positive number.

        Returns:
            float: The cleaned amount.

        Raises:
            forms.ValidationError: If the amount is not positive.
        """

        amount = self.cleaned_data.get('amount')

        if amount <= 0:
            raise forms.ValidationError("Amount must be a positive number.")
        return amount

    class Meta:
        model = Transaction
        fields = (
            'type',
            'amount',
            'currency',
            'date',
            'category',       
        )
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date'})
        }
