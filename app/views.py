from django.shortcuts import render, redirect, get_object_or_404

from app.models import Comments, Post, Tag, Profile, WebSiteMeta, Expense, Transaction, Category
from app.forms import CommentForm, SubscribeForm, NewUserForm, ExpenseForm, TransactionForm
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.contrib.auth.models import User
from django.db.models import Count, Sum
from django.contrib.auth import login, authenticate, logout
import datetime
from .utils import get_exchange_rates, convert_to_EUR
from django.contrib.auth.decorators import login_required
from django_htmx.http import retarget
from django.views.decorators.http import require_http_methods
from django.core.paginator import Paginator
from django.conf import settings

from app.filters import TransactionFilter

def post_page(request, slug):
    post = Post.objects.get(slug=slug)
    comments = Comments.objects.filter(post=post, parent=None)
    form = CommentForm()

    # Bookmark logic
    bookmarked = False
    if post.bookmarks.filter(id=request.user.id).exists():
        bookmarked = True
    is_bookmarked = bookmarked

    # Likes logic
    liked = False
    if post.likes.filter(id=request.user.id).exists():
        liked = True
    number_of_likes = post.number_of_likes()
    post_is_liked = liked
    
    if request.POST:
        comment_form = CommentForm(request.POST)
        if comment_form.is_valid:
            parent_obj = None
            if request.POST.get('parent'):
                # save reply
                parent = request.POST.get('parent')
                parent_obj = Comments.objects.get(id=parent)
                if parent_obj:
                    comment_reply = comment_form.save(commit=False)
                    comment_reply.parent = parent_obj
                    comment_reply.post = post
                    comment_reply.save()
                    return HttpResponseRedirect(reverse('post_page', kwargs={'slug':slug}))

            else:
                comment = comment_form.save(commit=False)
                postid = request.POST.get('post_id')
                post = Post.objects.get(id = postid)
                comment.post = post
                comment.save()
                return HttpResponseRedirect(reverse('post_page', kwargs={'slug':slug}))

    if post.view_count is None:
        post.view_count = 1
    else:
        post.view_count = post.view_count + 1
    post.save()

    
    context = {'post':post, 'form':form, 'comments':comments,
             'is_bookmarked':is_bookmarked, 
             'post_is_liked': post_is_liked,
             'number_of_likes': number_of_likes
             }
    return render(request, 'app/post.html', context)

def index(request):
    posts = Post.objects.all()
    top_posts = Post.objects.all().order_by('-view_count')[:3]
    recent_posts = Post.objects.all().order_by('-last_updated')[:3]
    featured_post = Post.objects.filter(is_featured=True)
    subscribe_form = SubscribeForm()
    subscribe_successful = None
    website_info = None

    # Fetching meta data if exists
    if WebSiteMeta.objects.all().exists():
        website_info = WebSiteMeta.objects.all()[0]

    if featured_post:
        featured_post = featured_post[0]

    if request.POST:
        subscribe_form = SubscribeForm(request.POST)
        if subscribe_form.is_valid():
            subscribe_form.save()

            # Do not render subscription form if form is submitted and saved to database
            request.session['subscribed'] = True
            subscribe_successful = 'Subscribed successfully!'
            subscribe_form = SubscribeForm()
            #return HttpResponseRedirect(reverse('index'))


    context = {'posts':posts, 'top_posts':top_posts, 'website_info':website_info, 'recent_posts':recent_posts, 'subscribe_form':subscribe_form, 'subscribe_successful' :subscribe_successful, 'featured_post':featured_post}
    return(render(request, 'app/index.html', context))


def tag_page(request, slug):
    tag = Tag.objects.get(slug=slug)

    top_posts = Post.objects.filter(tags__in=[tag.id]).order_by('-view_count')[:3]
    recent_posts = Post.objects.filter(tags__in=[tag.id]).order_by('-last_updated')[:3]
    
    tags = Tag.objects.all()
    context={'tag':tag, 'top_posts':top_posts, 'recent_posts':recent_posts, 'tags':tags}
    return(render(request, 'app/tag.html', context))


def author_page(request, slug):
    profile = Profile.objects.get(slug=slug)

    top_posts = Post.objects.filter(author=profile.user).order_by('-view_count')[:2]
    recent_posts = Post.objects.filter(author=profile.user).order_by('-last_updated')[:3]
    top_authors = User.objects.annotate(number=Count('post')).order_by('-number')

    profiles = Profile.objects.all()
    context = {'profile':profile, 'top_posts':top_posts, 'recent_posts':recent_posts, 'authors':profiles, 'top_authors':top_authors}
    return(render(request, 'app/author.html', context))

def search_posts(request):
    search_query=''
    if request.GET.get('q'):
        search_query = request.GET.get('q')
    posts = Post.objects.filter(title__icontains=search_query) | Post.objects.filter(content__icontains=search_query)
    print('Search:',search_query)
    context = {'posts':posts, 'search_query':search_query}
    return render(request, 'app/search.html', context)


def about(request):
    website_info = None

    # Fetching meta data if exists
    if WebSiteMeta.objects.all().exists():
        website_info = WebSiteMeta.objects.all()[0]

    context = {'website_info':website_info}
    return render(request, 'app/about.html', context)


def register_user(request):
    form = NewUserForm()
    if request.method == "POST":
        form = NewUserForm(request.POST)
        if form.is_valid():

            # Automatically login user after registration
            user = form.save()
            login(request, user)
            return redirect("/")

    context = {'form': form}
    return render(request, 'registration/registration.html', context)



def bookmark_post(request, slug):
    '''Toggles bookmarking: Adds or removes a post from the user's bookmarks.'''

    post = get_object_or_404(Post, id=request.POST.get('post_id'))
    if post.bookmarks.filter(id=request.user.id).exists():
        post.bookmarks.remove(request.user) # Remove bookmark if it exists
    else:
        post.bookmarks.add(request.user) # Add bookmark if it doesn't exist

    return HttpResponseRedirect(reverse('post_page', args=[str(slug)]))


def like_post(request, slug):
    '''Toggles like: Adds or removes a like from the post for the current user.'''

    post = get_object_or_404(Post, id=request.POST.get('post_id'))
    if post.likes.filter(id=request.user.id).exists():
        post.likes.remove(request.user) # Remove like if it exists
    else:
        post.likes.add(request.user) # Add like if it doesn't exist

    return HttpResponseRedirect(reverse('post_page', args=[str(slug)]))


def all_bookmarked_posts(request):
    '''Returns all bookmarked posts for the current user.'''

    bookmarked_posts = Post.objects.filter(bookmarks=request.user)
    context = {'bookmarked_posts': bookmarked_posts}
    return render(request, 'app/all_bookmarked_posts.html', context)


def my_posts(request):
    '''Returns all posts where the current user is the author.'''

    all_user_posts = Post.objects.filter(author=request.user)
    context = {'all_user_posts': all_user_posts}
    return render(request, 'app/my_posts.html', context)

def all_posts(request):
    '''Returns all posts.'''

    all_posts = Post.objects.all()
    context = {'all_posts': all_posts}
    return render(request, 'app/all_posts.html', context)


# def expense_tracker(request):

#     api_data = get_exchange_rates('SEK')
#     context = {'api_data': api_data}
#     return render(request, 'app/expense_tracker.html', context)
# def expense_tracker(request):
#     '''Function track all expenses and incomes.'''

#     if request.method == 'POST':
#         expense = ExpenseForm(request.POST)
#         if expense.is_valid():
#             expense.save()

    
#     expenses = Expense.objects.all()
#     total_expenses = expenses.aggregate(Sum('amount'))  

#     # Logic to calculate 365 days expenses
#     last_year = datetime.date.today() - datetime.timedelta(days=365)      
#     data_last_year = Expense.objects.filter(date__gt=last_year)
#     yearly_sum = data_last_year.aggregate(Sum('amount'))

#     # Logic to calculate 30 days expenses
#     last_30_days = datetime.date.today() - datetime.timedelta(days=30)      
#     data_last_30_days = Expense.objects.filter(date__gt=last_30_days)
#     monthly_sum = data_last_30_days.aggregate(Sum('amount'))

#     # Logic to calculate 7 days expenses
#     last_7_days = datetime.date.today() - datetime.timedelta(days=7)      
#     data_last_7_days = Expense.objects.filter(date__gt=last_7_days)
#     weekly_sum = data_last_7_days.aggregate(Sum('amount'))

#     daily_sums = Expense.objects.filter().values('date').order_by('date').annotate(sum=Sum('amount'))
#     categorical_sums = Expense.objects.filter().values('category').order_by('category').annotate(sum=Sum('amount'))

#     expense_form = ExpenseForm()
#     context = {'expense_form': expense_form, 'expenses': expenses,
#                'total_expenses':total_expenses,
#                'yearly_sum':yearly_sum,
#                'monthly_sum':monthly_sum,
#                'weekly_sum':weekly_sum,
#                'daily_sums':daily_sums,
#                'categorical_sums':categorical_sums
#      }
#     return render(request, 'app/expense_tracker.html', context) 


def edit(request, id):
    expense = Expense.objects.get(id=id)
    expense_form = ExpenseForm(instance = expense)

    if request.method == 'POST':
        expense = Expense.objects.get(id=id)
        form = ExpenseForm(request.POST, instance = expense)
        if form.is_valid():
            form.save()
            return redirect('expense_tracker')
        
    context = {'expense_form': expense_form}
    return render(request, 'app/edit.html', context) 

def delete(request, id):
    if request.method == 'POST' and ('delete' in request.POST):
        expense = Expense.objects.get(id=id)
        expense.delete()
    return redirect('expense_tracker')

@login_required
def transactions_list(request):
    transaction_filter = TransactionFilter(
        request.GET,
        queryset=Transaction.objects.filter(user=request.user).select_related('category')
    )

    total_income = transaction_filter.qs.get_total_income()
    total_expenses = transaction_filter.qs.get_total_expenses()
    context = {
        'filter': transaction_filter,
        'total_income': total_income,
        'total_expenses': total_expenses,
        'net_income': total_income - total_expenses
    }

    if request.htmx:
        print("It was HTMX")
        return render(request, 'app/partials/transactions-container.html', context)

    return render(request, 'app/transactions-list.html', context)


@login_required
def expense_tracker(request):

    all_transactions = Transaction.objects.all().filter(user=request.user).select_related('category')
    total_income = all_transactions.get_total_income()
    total_expenses = all_transactions.get_total_expenses()

    # Logic for filtering expenses
    transaction_filter = TransactionFilter(
        request.GET,
        queryset=Transaction.objects.filter(user=request.user).select_related('category')
    )
    paginator = Paginator(transaction_filter.qs, settings.PAGE_SIZE)  # Show 5 transactions per page.
    transaction_page = paginator.page(1) # Show the first page of results.

    total_income_filtered = transaction_filter.qs.get_total_income()
    total_expenses_filtered = transaction_filter.qs.get_total_expenses()
    context = {
        'filter': transaction_filter,
        'total_income_filtered': total_income_filtered,
        'total_expenses_filtered': total_expenses_filtered,
        'total_income': total_income,
        'total_expenses': total_expenses,
        'net_income': total_income - total_expenses,
        'transactions': transaction_page
    }

    if request.htmx:
        print("It was HTMX")
        return render(request, 'app/partials/expense_tracker_container.html', context)

    return render(request, 'app/expense_tracker.html', context)

@login_required
def create_transaction(request):

    # Initialize the form, passing the currencies as choices
    # form = TransactionForm()
    # form.fields['currency'].choices = currencies

    api_data = get_exchange_rates()
    if api_data:
        currencies = [(code, code) for code in api_data.keys()]
    else:
        currencies = []

    if request.method == 'POST':
        form = TransactionForm(request.POST, currencies=currencies)
        if form.is_valid():
            transaction = form.save(commit=False)
            transaction.user = request.user
            transaction.amount_in_usd = convert_to_EUR(transaction.amount, transaction.currency)
            transaction.save()
            context = {'message': "Transaction was added successfully!"}
            return render(request, 'app/partials/transaction-success.html', context)
        else:
            context = {'form': form}
            response = render(request, 'app/partials/create-transaction.html', context)
            return retarget(response, '#transaction-block')
    else:
        form = TransactionForm(currencies=currencies)

    context = {'form': form}
    return render(request, 'app/partials/create-transaction.html', context)


@login_required
def update_transaction(request, pk):
    '''Function to update a transaction'''
 
    api_data = get_exchange_rates()
    if api_data:
        currencies = [(code, code) for code in api_data.keys()]
    else:
        print('API IS DOWN')
        currencies = []

    transaction = get_object_or_404(Transaction, pk=pk, user=request.user)

    if request.method == 'POST':
        form = TransactionForm(request.POST, currencies=currencies, instance=transaction)
        if form.is_valid():
            transaction = form.save(commit=False)

            # Check if the 'amount' or 'currency' field has changed
            if form.has_changed() and ('amount' in form.changed_data or 'currency' in form.changed_data):
                transaction.amount_in_usd = convert_to_EUR(transaction.amount, transaction.currency)

            transaction.save()
            context = {'message': "Transaction was updated successfully!"}
            return render(request, 'app/partials/transaction-success.html', context)
        else:
            context = {'form': form}
            response =  render(request, 'app/update-transaction.html', context)
            return retarget(response, '#transaction-block')
    else:
        form = TransactionForm(currencies=currencies)



    context = {
        'form': TransactionForm(instance=transaction, currencies=currencies),
        'transaction': transaction,
    }
    return render(request, 'app/update-transaction.html', context)

@login_required
@require_http_methods(['DELETE'])
def delete_transaction(request, pk):
    '''Function to delete a transaction'''

    transaction = get_object_or_404(Transaction, pk=pk, user=request.user)
    transaction.delete()
    context = {'message': f'Transaction of {transaction.amount_in_usd} EUR on {transaction.date} was deleted successfully!'}
    return render(request, 'app/partials/transaction-success.html', context)


@login_required
def get_transactions(request):
    import time
    time.sleep(10)  # Simulate a delay of 1 second
    page = request.GET.get('page', 1)  # Get the page number from the query parameters, default to 1 if not provided
        # Logic for filtering expenses
    transaction_filter = TransactionFilter(
        request.GET,
        queryset=Transaction.objects.filter(user=request.user).select_related('category')
    )
    paginator = Paginator(transaction_filter.qs, settings.PAGE_SIZE)  # Show 5 transactions per page.

    context = {
        'transactions': paginator.page(page)  # Get the transactions for the specified page
    }
    return render(
        request,
        'app/partials/expense_tracker_container.html#transaction_list',
        context
    )


def view_statistic(request):
    '''Function to view statistics'''

    # Get the date 30 days ago from today
    last_30_days = datetime.date.today() - datetime.timedelta(days=30)

    # Get the total expenses the last 30 days
    expense_data_last_30_days = Transaction.objects.filter(date__gt=last_30_days, type='expense', user=request.user)
    last_month_expenses = expense_data_last_30_days.aggregate(Sum('amount_in_usd'))

    # Get the total income the last 30 days
    income_data_last_30_days = Transaction.objects.filter(date__gt=last_30_days, type='income', user=request.user)
    last_month_income = income_data_last_30_days.aggregate(Sum('amount_in_usd'))

    # Get total sum by category for the last 30 days
    category_names = []
    category_sums = []

    expenses_by_category_last_30_days = Transaction.objects.filter(date__gt=last_30_days, type='expense', user=request.user).values('category').order_by('category').annotate(sum=Sum('amount_in_usd'))
    
    for expense in expenses_by_category_last_30_days:
        category_name = Category.objects.get(id=expense['category']).name
        category_names.append(category_name)
        category_sums.append(expense['sum'])
    
    # Get total sum by day for the last 30 days
    last_7_days_dates = []
    last_7_days_sums = []
    expenses_by_day_last_30_days = Transaction.objects.filter(date__gt=last_30_days, type='expense', user=request.user).values('date').order_by('date').annotate(sum=Sum('amount_in_usd'))

    for expense in expenses_by_day_last_30_days:
        last_7_days_dates.append(expense['date'])
        last_7_days_sums.append(expense['sum'])

    context = {
        'category_names': category_names,
        'category_sums': category_sums,
        'last_7_days_dates': last_7_days_dates,
        'last_7_days_sums': last_7_days_sums,
        'last_month_expenses' : last_month_expenses,
        'last_month_income' : last_month_income,
    }
    
    #context = {}
    return render(request, 'app/statistic.html', context)
