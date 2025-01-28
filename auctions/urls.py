from django.urls import path, re_path
from django.views.generic.base import RedirectView

from . import views

app_name = "auctions"

urlpatterns = [
    path("", views.index, name="index"),
    re_path(r'^all/?$', views.all_listings, name="all_listings"),
    re_path(r'^my-listings/?$', views.my_listings, name="my_listings"),
    re_path(r'^my-watchlist/?$', views.watchlist, name="watchlist"),
    re_path(r'^new/?$', views.new_listing, name="new_listing"),
    re_path(r'^listing/(?P<listing_id>[0-9]+)/?$', views.listing_page, name="listing_page"),
    re_path(r"^login/?$", views.login_view, name="login"),
    re_path(r"^logout/?$", views.logout_view, name="logout"),
    re_path(r"^register/?$", views.register, name="register"),
    re_path(r'^.+/?$', RedirectView.as_view(pattern_name='auctions:index', permanent=True))
]
