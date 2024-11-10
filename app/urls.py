"""
URL configuration for the app.

This module defines the URL patterns for the app, mapping each URL to a specific view.
"""

from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('post/<slug:slug>', views.post_page, name='post_page'),
    path('tag/<slug:slug>', views.tag_page, name='tag_page'),
    path('author/<slug:slug>', views.author_page, name='author_page'),
    path('search/', views.search_posts, name='search'),
    path('about/', views.about, name='about'),
    path('accounts/register', views.register_user, name='register'),
    path('bookmark_post/<slug:slug>', views.bookmark_post, name='bookmark_post'),
    path('like_post/<slug:slug>', views.like_post, name='like_post'),
    path('all_bookmarked_posts', views.all_bookmarked_posts, name='all_bookmarked_posts'),
    path('my_posts', views.my_posts, name='my_posts'),
    path('all_posts', views.all_posts, name='all_posts'),
    path('expense_tracker', views.expense_tracker, name='expense_tracker'),
    path('transactions', views.transactions_list, name='transactions'),
    path('transactions/create/', views.create_transaction, name='create-transaction'),
    path('transactions/<int:pk>/update/', views.update_transaction, name='update-transaction'),
    path('transactions/<int:pk>/delete/', views.delete_transaction, name='delete-transaction'),
    path('get-transactions/', views.get_transactions, name='get-transactions'),
    path('statistic', views.view_statistic, name='statistic'),
]
