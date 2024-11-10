"""
App configuration for the 'app' Django application.

This module defines the configuration for the 'app' app, including the default
auto field type for model primary keys.
"""


from django.apps import AppConfig


class AppConfig(AppConfig):

    # Set the default primary key field type for models in this app
    default_auto_field = "django.db.models.BigAutoField"

    # Define the name of the app, which Django uses for routing and configuration
    name = "app"
