from colorfield.fields import ColorField
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.translation import gettext_lazy as _


class Category(models.Model):
    class Meta:
        verbose_name = "Category"
        verbose_name_plural = "Categories"

    category_name = models.CharField(max_length=20)
    color = ColorField(default='#ffffff')
    color_text = ColorField(default='#000000')

    def __str__(self):
        return f'{self.category_name}'


class Listing(models.Model):
    class ListingState(models.TextChoices):
        ACTIVE = 'A', _('Active')
        CLOSED = 'C', _('Closed')

    title = models.CharField(max_length=100)
    starting_price = models.DecimalField(max_digits=10, decimal_places=2)
    description = models.TextField()
    state = models.CharField(
        max_length=1, choices=ListingState.choices, default=ListingState.ACTIVE)
    image_url = models.URLField(blank=True, null=True)
    category = models.ForeignKey(
        'Category', blank=True, on_delete=models.SET_NULL, null=True, related_name='listing_category')
    user = models.ForeignKey(
        'User', on_delete=models.CASCADE, related_name='listing_user')
    bids = models.ManyToManyField('User', through='Bid', related_name='listing_bids')
    comments = models.ManyToManyField(
        'User', through='Comment', related_name='listing_comments')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'{self.title}'


class Bid(models.Model):
    listing = models.ForeignKey(
        'Listing', on_delete=models.CASCADE, related_name='bid_listing')
    user = models.ForeignKey(
        'User', on_delete=models.CASCADE, related_name='bid_user')
    price = models.DecimalField(max_digits=10, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'${self.price}'


class Comment(models.Model):
    listing = models.ForeignKey(
        'Listing', on_delete=models.CASCADE, related_name='comment_listing')
    user = models.ForeignKey(
        'User', on_delete=models.CASCADE, related_name='comment_user')
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'{self.content}'


class User(AbstractUser):
    watchlist = models.ManyToManyField(
        'Listing', blank=True, related_name='user_watchlist')

    def __str__(self):
        return f'{self.first_name} {self.last_name} a.k.a. {self.username}'
