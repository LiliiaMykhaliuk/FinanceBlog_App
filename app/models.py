"""
Django models for user profiles, blog posts, subscriptions, transactions, and website metadata.

This module includes models for user profiles, subscription management, blog posts,
comments, transaction records, and website metadata for a finance or blogging application.
It also includes custom managers and methods to handle functionality such as slug generation,
like counts, and transaction filtering.
"""


from django.db import models
from django.utils.text import slugify
from django.contrib.auth.models import User

# Local import
from .managers import TransactionQuerySet


class Profile(models.Model):
    """
    User profile model to store additional information for each user, such as
    profile image, biography, and a unique slug for URL identification.
    """

    user = models.OneToOneField(User, on_delete=models.CASCADE)
    profile_image = models.ImageField(null=True, blank=True, upload_to= "images/")
    slug = models.SlugField(max_length=200, unique=True)
    bio = models.CharField(max_length=200)

    def save(self, *args, **kwargs):
        """
        Override save method to automatically generate a slug from the username
        if this is a new profile.
        """

        if not self.id:
            self.slug = slugify(self.user.username)
        return super(Profile, self).save(*args, **kwargs)

    def __str__(self):
        """
        Return the user's first name as the string representation of the profile.
        """
        return self.user.first_name


class Subscribe(models.Model):
    """
    Model to store email subscriptions for the website.
    """
    email = models.EmailField(max_length=200, unique=True)
    date = models.DateTimeField(auto_now_add=True)


class Tag(models.Model):
    """
    Model to represent tags for blog posts. Tags can be used to categorize or label posts.
    """

    name = models.CharField(max_length=100)
    description = models.CharField(max_length=100)
    slug = models.SlugField(max_length=200, unique=True)

    def save(self, *args, **kwargs):
        """
        Override save method to automatically generate a slug from the tag name
        if this is a new tag.
        """

        if not self.id:
            self.slug = slugify(self.name)
        return super(Tag, self).save(*args, **kwargs)

    def __str__(self):
        """
        Return the tag name as the string representation of the tag.
        """
        return self.name


class Post(models.Model):
    """
    Model representing a blog post. Each post can have multiple tags, be authored by a user,
    and be bookmarked or liked by users.
    """

    title = models.CharField(max_length=200)
    content = models.TextField()
    last_updated = models.DateTimeField(auto_now=True)
    slug = models.SlugField(max_length=200, unique=True)
    image = models.ImageField(null=True, blank=True, upload_to= "images/")
    tags = models.ManyToManyField(Tag, blank=True, related_name='post')
    view_count = models.IntegerField(null=True, blank=True)
    is_featured = models.BooleanField(default=False)
    author = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    bookmarks = models.ManyToManyField(User, related_name='bookmarks', default=None, blank=True)
    likes = models.ManyToManyField(User, related_name='likes', default=None, blank=True)


    def number_of_likes(self):
        """
        Return the number of likes the post has received.
        """

        return self.likes.count

    def __str__(self):
        """
        Return the post's title as its string representation.
        """

        return self.title


class Comments(models.Model):
    """
    Model representing comments made on blog posts. Comments can be made by users
    and can have replies (parent-child relationships).
    """

    content = models.TextField()
    date = models.DateTimeField(auto_now=True)
    name = models.CharField(max_length=200)
    email = models.EmailField(max_length=200)
    website = models.CharField(max_length=200)
    post = models.ForeignKey(Post, on_delete=models.CASCADE)
    author = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    parent = models.ForeignKey('self', on_delete=models.DO_NOTHING, null=True, blank=True, related_name='replies')


class WebSiteMeta(models.Model):
    """
    Model to store website metadata like title, description, and about section.
    """


    title = models.CharField(max_length=200)
    description = models.CharField(max_length=500)
    about = models.TextField()


class Category(models.Model):
    """
    Model to represent categories for financial transactions in finance tracker (e.g., food, bills).
    """

    name = models.CharField(max_length=50, unique=True)

    class Meta:
        """
        Meta options for Category model, including verbose name and plural name for admin interface.
        """
        verbose_name_plural = 'Categories'

    def __str__(self):
        """
        Return the category name as its string representation.
        """
        return self.name


class Transaction(models.Model):
    """
    Model to represent a financial transaction in finance tracker.

    Each transaction has a type (income or expense), an amount, currency, and date,
    as well as a link to the user and category.
    """

    TRANSACTION_TYPE_CHOICES = (
        ('income', 'Income'),
        ('expense', 'Expense'),
    )

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    type = models.CharField(max_length=7, choices=TRANSACTION_TYPE_CHOICES)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=100)
    amount_in_usd = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    date = models.DateField()

    # Using custom manager for transaction filtering
    objects = TransactionQuerySet.as_manager()

    def __str__(self):
        """
        Return a string representation of the transaction, including type, amount, currency, 
        date, and user.
        """

        return f"{self.type} of {self.amount_in_usd} {self.currency} on {self.date} by {self.user}"

    class Meta:
        """
        Meta options for ordering transactions by date in descending order.
        """

        ordering = ['-date']
