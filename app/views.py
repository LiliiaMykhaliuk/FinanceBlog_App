"""
Django views for handling the post page, index page, and related user interactions.

This module includes views that render the post page, allow users to comment on posts, 
like or bookmark posts, and manage subscription. It also includes the logic for rendering 
the homepage, displaying top posts, recent posts, and featured posts.

The views utilize models like Post, Comments, and WebSiteMeta, and provide forms for user 
interaction such as subscribing and commenting.
"""


import datetime
import time

from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponseRedirect
from django.urls import reverse
from django_htmx.http import retarget
from django.views.decorators.http import require_http_methods
from django.core.paginator import Paginator
from django.conf import settings

from django.contrib.auth.models import User
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Sum

from app.models import Comments, Post, Tag, Profile, WebSiteMeta, Transaction, Category
from app.forms import CommentForm, SubscribeForm, NewUserForm, TransactionForm
from app.filters import TransactionFilter
from .utils import get_exchange_rates, convert_to_EUR


def post_page(request, slug):
    """
    View to render a specific post page along with comments, bookmarks, likes, and comment functionality.

    Handles the display of the post, comment submission, like and bookmark status, and tracks the number of views.

    Args:
        request: The HTTP request object.
        slug (str): The unique slug identifier for the post.

    Returns:
        HttpResponse: The rendered post page with context.
    """

    # Fetch the post object based on the slug
    post = Post.objects.get(slug=slug)

    # Retrieve top-level comments for the post
    comments = Comments.objects.filter(post=post, parent=None)

    # Initialize comment form for new comment submissions
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
    
    # Handle comment form submission
    if request.POST:
        comment_form = CommentForm(request.POST)
        if comment_form.is_valid:
            parent_obj = None

            if request.POST.get('parent'):

                # Save reply to an existing comment
                parent = request.POST.get('parent')
                parent_obj = Comments.objects.get(id=parent)

                if parent_obj:
                    comment_reply = comment_form.save(commit=False)
                    comment_reply.parent = parent_obj
                    comment_reply.post = post
                    comment_reply.save()
                    return HttpResponseRedirect(reverse('post_page', kwargs={'slug':slug}))

            else:
                # Save a new comment
                comment = comment_form.save(commit=False)
                postid = request.POST.get('post_id')
                post = Post.objects.get(id = postid)
                comment.post = post
                comment.save()
                return HttpResponseRedirect(reverse('post_page', kwargs={'slug':slug}))

    # Update view count for the post
    if post.view_count is None:
        post.view_count = 1
    else:
        post.view_count = post.view_count + 1
    post.save()

    # Retrieve top posts based on view count (ordered in descending order)
    top_posts = Post.objects.all().order_by('-view_count')[:3]

    # Retrieve recent posts ordered by last updated
    recent_posts = Post.objects.all().order_by('-last_updated')[:3]

    # Context data for rendering the post page
    context = {
        'post':post,
        'form':form,
        'comments':comments,
        'is_bookmarked':is_bookmarked, 
        'post_is_liked': post_is_liked,
        'number_of_likes': number_of_likes,
        'top_posts': top_posts,
        'recent_posts': recent_posts,
    }
    return render(request, 'app/post.html', context)


def index(request):
    """
    View to render the homepage with lists of posts, featured content, and subscription form.

    Displays all posts, top posts by view count, recent posts, and a featured post.
    It also handles the subscription form submission.

    Args:
        request: The HTTP request object.

    Returns:
        HttpResponse: The rendered homepage with context.
    """

    # Fetch all posts
    posts = Post.objects.all()

    # Retrieve top posts based on view count (ordered in descending order)
    top_posts = Post.objects.all().order_by('-view_count')[:3]

    # Retrieve recent posts ordered by last updated
    recent_posts = Post.objects.all().order_by('-last_updated')[:3]

    # Fetch the featured post
    featured_post = Post.objects.filter(is_featured=True)

    # Initialize the subscription form and set success message to None initially
    subscribe_form = SubscribeForm()
    subscribe_successful = None
    website_info = None

    # Fetch website meta data if it exists
    if WebSiteMeta.objects.all().exists():
        website_info = WebSiteMeta.objects.all()[0]

    # If there's a featured posts in database, set it to the first one in the queryset
    if featured_post:
        featured_post = featured_post[0]

    # Handle subscription form submission
    if request.POST:
        subscribe_form = SubscribeForm(request.POST)
        if subscribe_form.is_valid():
            subscribe_form.save()

            # Set session variable to indicate that subscription was submitted
            # and display success message
            request.session['subscribed'] = True
            subscribe_successful = 'Subscribed successfully!'
            subscribe_form = SubscribeForm()

    # Context data for rendering the homepage
    context = {
        'posts':posts,
        'top_posts':top_posts,
        'website_info':website_info,
        'recent_posts':recent_posts,
        'subscribe_form':subscribe_form,
        'subscribe_successful' :subscribe_successful,
        'featured_post':featured_post
    }
    return render(request, 'app/index.html', context)


def tag_page(request, slug):
    """
    View to render a page displaying posts related to a specific tag.

    Fetches and displays the tag, top posts associated with the tag, 
    recent posts related to the tag, and a list of all available tags.

    Args:
        request: The HTTP request object.
        slug (str): The slug of the tag to be displayed.

    Returns:
        HttpResponse: The rendered tag page with context.
    """

    # Fetch the tag object based on the slug
    tag = Tag.objects.get(slug=slug)

    # Retrieve top posts with fetched tag ordered by view count
    top_posts = Post.objects.filter(tags__in=[tag.id]).order_by('-view_count')[:3]

    # Retrieve recent posts with fetched tag ordered by last updated
    recent_posts = Post.objects.filter(tags__in=[tag.id]).order_by('-last_updated')[:3]
    
    # Get all available tags
    tags = Tag.objects.all()

    # Context data for rendering the tag page
    context={
        'tag':tag,
        'top_posts':top_posts,
        'recent_posts':recent_posts,
        'tags':tags
    }
    return render(request, 'app/tag.html', context)


def author_page(request, slug):
    """
    View to render a page displaying posts related to a specific author.

    Fetches and displays the author's profile, top posts written by the author,
    recent posts written by the author, top authors based on the number of posts written, 
    and a list of all authors.

    Args:
        request: The HTTP request object.
        slug (str): The slug of the author's profile to be displayed.

    Returns:
        HttpResponse: The rendered author page with context.
    """

    # Fetch the profile of the author based on the slug
    profile = Profile.objects.get(slug=slug)

    # Retrieve top posts by the author, ordered by view count
    top_posts = Post.objects.filter(author=profile.user).order_by('-view_count')[:2]

    # Retrieve recent posts by the author, ordered by last updated
    recent_posts = Post.objects.filter(author=profile.user).order_by('-last_updated')[:3]

    # Retrieve top authors, ordered by the number of posts written
    top_authors = User.objects.annotate(number=Count('post')).order_by('-number')

    # Get all profiles for displaying the authors
    profiles = Profile.objects.all()

    # Context data for rendering the author page
    context = {
        'profile':profile,
        'top_posts':top_posts,
        'recent_posts':recent_posts,
        'authors':profiles,
        'top_authors':top_authors
    }
    return(render(request, 'app/author.html', context))


def search_posts(request):
    """
    View to handle the search functionality for posts.

    Searches posts based on a query parameter ('q') in the GET request.
    Displays posts whose title or content contains the search query.

    Args:
        request: The HTTP request object.

    Returns:
        HttpResponse: The rendered search page with the search results and query.
    """

    # Initialize search query to an empty string if no query is provided
    search_query=''
    if request.GET.get('q'):
        search_query = request.GET.get('q')
    
    # Perform a search in both title and content of posts, case-insensitive
    posts = Post.objects.filter(title__icontains=search_query) | Post.objects.filter(content__icontains=search_query)

    # !!!!!!!!!!!!!!! ----REMOVE in production
    print('Search:',search_query)

    # Context data for rendering the search results page
    context = {'posts':posts, 'search_query':search_query}
    return render(request, 'app/search.html', context)


def about(request):
    """
    View to render the 'About' page.

    Fetches the website metadata, if it exists, and displays it on the 'About' page.
    
    Args:
        request: The HTTP request object.

    Returns:
        HttpResponse: The rendered about page with website metadata context.
    """

    website_info = None

    # Fetching meta data if exists
    if WebSiteMeta.objects.all().exists():
        website_info = WebSiteMeta.objects.all()[0]

    # Context data for rendering the search results page
    context = {'website_info':website_info}
    return render(request, 'app/about.html', context)


def register_user(request):
    """
    View to handle user registration.

    Renders a form for new users to register, and automatically logs in the user upon successful registration.

    Args:
        request: The HTTP request object.

    Returns:
        HttpResponse: The rendered registration page with the registration form or 
                      a redirect to the homepage after successful registration.
    """

    form = NewUserForm()
    if request.method == "POST":
        form = NewUserForm(request.POST)
        if form.is_valid():

            # Save user and log them in
            user = form.save()
            login(request, user)
            return redirect("/")

    # Context data for rendering the search results page
    context = {'form': form}
    return render(request, 'registration/registration.html', context)


def bookmark_post(request, slug):
    """
    View to toggle a bookmark on a post for the current user.

    Args:
        request: The HTTP request object.
        slug (str): The slug of the post to be bookmarked.

    Returns:
        HttpResponseRedirect: Redirects back to the post page.
    """

    post = get_object_or_404(Post, id=request.POST.get('post_id'))
    if post.bookmarks.filter(id=request.user.id).exists():
        post.bookmarks.remove(request.user) # Remove bookmark if it exists
    else:
        post.bookmarks.add(request.user) # Add bookmark if it doesn't exist

    # Context data for rendering the search results page
    return HttpResponseRedirect(reverse('post_page', args=[str(slug)]))


def like_post(request, slug):
    """
    View to toggle a like on a post for the current user.

    Args:
        request: The HTTP request object.
        slug (str): The slug of the post to be liked.

    Returns:
        HttpResponseRedirect: Redirects back to the post page.
    """

    post = get_object_or_404(Post, id=request.POST.get('post_id'))
    if post.likes.filter(id=request.user.id).exists():
        post.likes.remove(request.user) # Remove like if it exists
    else:
        post.likes.add(request.user) # Add like if it doesn't exist
    
    return HttpResponseRedirect(reverse('post_page', args=[str(slug)]))


def all_bookmarked_posts(request):
    """
    View to display all posts bookmarked by the current user.

    Args:
        request: The HTTP request object.

    Returns:
        HttpResponse: The rendered bookmarked posts page.
    """

    bookmarked_posts = Post.objects.filter(bookmarks=request.user)

    # Context data for rendering the search results page
    context = {'bookmarked_posts': bookmarked_posts}
    return render(request, 'app/all_bookmarked_posts.html', context)


def my_posts(request):
    """
    View to display all posts authored by the current user.

    Args:
        request: The HTTP request object.

    Returns:
        HttpResponse: The rendered user posts page.
    """

    all_user_posts = Post.objects.filter(author=request.user)

    # Context data for rendering the search results page
    context = {'all_user_posts': all_user_posts}
    return render(request, 'app/my_posts.html', context)


def all_posts(request):
    """
    View to display all posts.

    Args:
        request: The HTTP request object.

    Returns:
        HttpResponse: The rendered all posts page.
    """

    all_posts = Post.objects.all()

    # Context data for rendering the search results page
    context = {'all_posts': all_posts}

    return render(request, 'app/all_posts.html', context)


@login_required
def transactions_list(request):
    """
    View to display filtered list of transactions for the current user.
    Supports HTMX requests for partial page rendering.
    """

    transaction_filter = TransactionFilter(
        request.GET,
        queryset=Transaction.objects.filter(user=request.user).select_related('category')
    )

    total_income = transaction_filter.qs.get_total_income()
    total_expenses = transaction_filter.qs.get_total_expenses()

    # Context data for rendering the search results page
    context = {
        'filter': transaction_filter,
        'total_income': total_income,
        'total_expenses': total_expenses,
        'net_income': total_income - total_expenses
    }

    if request.htmx:
        return render(request, 'app/partials/transactions-container.html', context)

    return render(request, 'app/transactions-list.html', context)


@login_required
def expense_tracker(request):
    """
    View to display a paginated and filtered list of transactions with income/expense summary.
    Supports HTMX requests for partial page rendering.
    """

    all_transactions = Transaction.objects.all().filter(user=request.user).select_related('category')
    total_income = all_transactions.get_total_income()
    total_expenses = all_transactions.get_total_expenses()

    # Logic for filtering expenses
    transaction_filter = TransactionFilter(
        request.GET,
        queryset=Transaction.objects.filter(user=request.user).select_related('category')
    )

    # Handle pagination
    paginator = Paginator(transaction_filter.qs, settings.PAGE_SIZE)  # Show 5 transactions per page.
    transaction_page = paginator.page(1) # Show the first page of results.

    # Filtered totals
    total_income_filtered = transaction_filter.qs.get_total_income()
    total_expenses_filtered = transaction_filter.qs.get_total_expenses()

    # Context data for rendering the search results page
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
        return render(request, 'app/partials/expense_tracker_container.html', context)

    return render(request, 'app/expense_tracker.html', context)


@login_required
def create_transaction(request):
    """
    Creates a new transaction for the user with a form that dynamically loads currency options.
    """

    # Fetch available currencies from an API.
    api_data = get_exchange_rates()
    if api_data:
        currencies = [(code, code) for code in api_data.keys()]  # Dynamically set currency choices
    else:
        currencies = []

    if request.method == 'POST':

        # Initialize the form with posted data and dynamic currency choices
        form = TransactionForm(request.POST, currencies=currencies)

        # Check if form data is valid
        if form.is_valid():

            # Create transaction instance without saving to add user and converted amount
            transaction = form.save(commit=False)
            transaction.user = request.user # Associate transaction with the current user

            # Convert transaction amount to EUR and save it to `amount_in_usd` field
            transaction.amount_in_usd = convert_to_EUR(transaction.amount, transaction.currency)
            transaction.save()  # Save the transaction to the database

            # Render a success message on successful transaction creation
            context = {'message': "Transaction was added successfully!"}
            return render(request, 'app/partials/transaction-success.html', context)
        else:
            # Render form with error messages if invalid
            context = {'form': form}
            response = render(request, 'app/partials/create-transaction.html', context)
            return retarget(response, '#transaction-block')

    else:
        # For GET requests, initialize an empty form with dynamic currency choices
        form = TransactionForm(currencies=currencies)

    context = {'form': form}
    return render(request, 'app/partials/create-transaction.html', context)


@login_required
def update_transaction(request, pk):
    """
    Handles the update of an existing transaction for the current user.

    This view fetches available currencies from an API to populate choices in the transaction form.
    If the form is valid and either 'amount' or 'currency' has changed, it recalculates the 
    `amount_in_usd` before saving. If invalid, it re-renders the form with error messages.
    """
 
    # Fetch available currencies from an external API
    api_data = get_exchange_rates()
    if api_data:
        currencies = [(code, code) for code in api_data.keys()] # Default to empty list if API fails
    else:
        print('API IS DOWN')
        currencies = []

    # Retrieve the transaction to be updated, ensuring it belongs to the current user
    transaction = get_object_or_404(Transaction, pk=pk, user=request.user)

    if request.method == 'POST':

        # Initialize the form with POST data, currency choices, and the existing transaction instance
        form = TransactionForm(request.POST, currencies=currencies, instance=transaction)

        # Check if the form data is valid
        if form.is_valid():
            transaction = form.save(commit=False) # Prepare to save but hold off to allow further changes

            # Recalculate `amount_in_usd` if either 'amount' or 'currency' has changed
            if form.has_changed() and ('amount' in form.changed_data or 'currency' in form.changed_data):
                transaction.amount_in_usd = convert_to_EUR(transaction.amount, transaction.currency)

            transaction.save()  # Save the updated transaction to the database

            # Render a success message if update was successful
            context = {'message': "Transaction was updated successfully!"}
            return render(request, 'app/partials/transaction-success.html', context)
        else:
            # Render form with errors if form data is invalid
            context = {'form': form}
            response =  render(request, 'app/update-transaction.html', context)
            return retarget(response, '#transaction-block')
    else:
        # For GET requests, initialize a form with the existing transaction instance and currency choices
        form = TransactionForm(currencies=currencies)


    # Render the update transaction form with the existing transaction data
    context = {
        'form': TransactionForm(instance=transaction, currencies=currencies),
        'transaction': transaction,
    }
    return render(request, 'app/update-transaction.html', context)


@login_required
@require_http_methods(['DELETE'])
def delete_transaction(request, pk):
    """
    Handle deletion of a specific transaction for the current user.

    This view deletes a transaction instance if it belongs to the logged-in user.
    After deletion, it renders a success message displaying the deleted transaction's
    amount in EUR and date.
    """

    # Retrieve the transaction by primary key, ensuring it belongs to the current user
    transaction = get_object_or_404(Transaction, pk=pk, user=request.user)

    # Delete the retrieved transaction from the database
    transaction.delete()

    # Context message with confirmation details of the deleted transaction
    context = {'message': f'Transaction of {transaction.amount_in_usd} EUR on {transaction.date} was deleted successfully!'}

    # Render the success message in the specified template
    return render(request, 'app/partials/transaction-success.html', context)


@login_required
def get_transactions(request):
    """
    Fetch and paginate transactions for the current user, rendering the results.

    This view applies filtering and pagination to the user's transactions based on
    query parameters. It returns the specified page of filtered transactions, allowing
    for dynamic reloading and rendering in the expense tracker interface.
    """

    time.sleep(10)  # Simulate a delay of 1 second

    # Get the requested page number from query parameters; default to page 1 if unspecified
    page = request.GET.get('page', 1)
    
    # Apply filtering to transactions based on user and query parameters
    transaction_filter = TransactionFilter(
        request.GET,
        queryset=Transaction.objects.filter(user=request.user).select_related('category')
    )

    # Paginate the filtered queryset with the defined page size
    paginator = Paginator(transaction_filter.qs, settings.PAGE_SIZE)  # Show 5 transactions per page.

    # Context dictionary for rendering the template with paginated transactions
    context = {
        'transactions': paginator.page(page)  # Get the transactions for the specified page
    }

    # Render the filtered and paginated transactions to a specific section in the template
    return render(
        request,
        'app/partials/expense_tracker_container.html#transaction_list',
        context
    )


@login_required
def view_statistic(request):
    """
    Display a summary of financial statistics for the current user.

    This view calculates and aggregates data on income, expenses, spending per category,
    and daily expenses. The results are then passed to the context
    for rendering on the statistics page.
    """

    # Calculate the date 30 days ago from today
    last_30_days = datetime.date.today() - datetime.timedelta(days=30)

    # Query for total expenses over the last 30 days
    expense_data_last_30_days = Transaction.objects.filter(date__gt=last_30_days, type='expense', user=request.user)
    last_month_expenses = expense_data_last_30_days.aggregate(Sum('amount_in_usd'))

    # Query for total income over the last 30 days
    income_data_last_30_days = Transaction.objects.filter(date__gt=last_30_days, type='income', user=request.user)
    last_month_income = income_data_last_30_days.aggregate(Sum('amount_in_usd'))

    # Aggregate expenses by category over the last 30 days
    category_names = []
    category_sums = []

    expenses_by_category_last_30_days = (
        Transaction.objects
        .filter(date__gt=last_30_days, type='expense', user=request.user)
        .values('category').order_by('category')
        .annotate(sum=Sum('amount_in_usd'))
    )

    # Retrieve category names and corresponding sums
    for expense in expenses_by_category_last_30_days:
        category_name = Category.objects.get(id=expense['category']).name
        category_names.append(category_name)
        category_sums.append(expense['sum'])
    
    # Aggregate expenses by day over the last 30 days
    last_7_days_dates = []
    last_7_days_sums = []
    expenses_by_day_last_30_days = (
        Transaction.objects
        .filter(date__gt=last_30_days, type='expense', user=request.user)
        .values('date')
        .order_by('date')
        .annotate(sum=Sum('amount_in_usd'))
    )

    # Retrieve dates and corresponding sums for daily expenses over the last 30 days
    for expense in expenses_by_day_last_30_days:
        last_7_days_dates.append(expense['date'])
        last_7_days_sums.append(expense['sum'])

    # Compile data into the context dictionary for template rendering
    context = {
        'category_names': category_names,
        'category_sums': category_sums,
        'last_7_days_dates': last_7_days_dates,
        'last_7_days_sums': last_7_days_sums,
        'last_month_expenses' : last_month_expenses,
        'last_month_income' : last_month_income,
    }
    
    # Render the statistics page with the aggregated data
    return render(request, 'app/statistic.html', context)
