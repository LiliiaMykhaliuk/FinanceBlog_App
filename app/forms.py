
from django import forms
from app.models import Comments, Subscribe, Expense, Transaction, Category
from django.utils.translation import gettext_lazy as _
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User


class CommentForm(forms.ModelForm):
    class Meta:
        model = Comments
        fields = {'content', 'email', 'name', 'website'}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['content'].widget.attrs['placeholder'] = 'Type your comment...'
        self.fields['email'].widget.attrs['placeholder'] = 'Email'
        self.fields['name'].widget.attrs['placeholder'] = 'Name'
        self.fields['website'].widget.attrs['placeholder'] = 'Website'


class SubscribeForm(forms.ModelForm):
    class Meta:
        model = Subscribe
        fields = '__all__'
        labels = {'email':_('')}

    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['email'].widget.attrs['placeholder'] = 'Enter your email'


class NewUserForm(UserCreationForm):
    class Meta:
        model = User
        fields = ("username", "email", "password1", "password2")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].widget.attrs['placeholder'] = 'Username'
        self.fields['email'].widget.attrs['placeholder'] = 'Email'
        self.fields['password1'].widget.attrs['placeholder'] = 'Password'
        self.fields['password2'].widget.attrs['placeholder'] = 'Repeat password'

    def clean_username(self):
        username = self.cleaned_data['username'].lower()  
        new = User.objects.filter(username = username)
        if new.count():
            raise forms.ValidationError("User Already Exist")
        return username

    def clean_email(self):
        email = self.cleaned_data['email'].lower()  
        new = User.objects.filter(email = email)
        if new.count():
            raise forms.ValidationError("Email Already Exist")
        return email

    def clean_password2(self):
        password1 = self.cleaned_data['password1']
        password2 = self.cleaned_data['password2']

        if password1 and password2 and password1 != password2:
            raise forms.ValidationError("Passwords don't match")
        return password2


class ExpenseForm(forms.ModelForm):
    class Meta:
        model = Expense
        fields = ['name', 'amount', 'category']



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

    category = forms.ModelChoiceField(
        queryset=Category.objects.all(),
        widget=forms.RadioSelect()
    )

    currency = forms.ChoiceField(choices=DEFAULT_CURRENCIES, required=True)  # Empty by default, populated in the view

    def __init__(self, *args, currencies=None, **kwargs):
        super(TransactionForm, self).__init__(*args, **kwargs)
        if currencies:
            # If dynamic currencies are passed, override default choices
            self.fields['currency'].choices = currencies
        else:
            # Fallback to default currencies
            self.fields['currency'].choices = DEFAULT_CURRENCIES

    def clean_amount(self):
        '''Ensure the amount is a positive number.'''

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
