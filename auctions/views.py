from decimal import Decimal

from django import forms
from django.forms.utils import ErrorList
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.db import IntegrityError
from django.db.models import Max
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render, redirect
from django.urls import reverse

from .models import User, Listing, Category, Comment, Bid


# Forms

class DivErrorList(ErrorList):
    def __str__(self):
        if not self:
            return ''
        return '<div class="errorlist alert alert-danger">%s</div>' % \
            ''.join(['<div class="error">%s</div>' % e for e in self])


class TextAreaForm(forms.Form):
    content = forms.CharField(label='', widget=forms.Textarea(attrs={
        'class': 'form-control',
        'rows': 4,
        'placeholder': 'Add your comment here...',
        'required': True}))


class InputForm(forms.Form):
    bid_price = forms.CharField(label='', widget=forms.TextInput(attrs={
        'class': 'form-control',
        'type': 'number',
        'placeholder': 'Place your Bid (0.00)*',
        'step': 0.01,
        'min': 0.01,
        'required': True}))


# Views

def index(request):
    if request.method == "POST":
        return _add_remove_from_watchlist(request, index.__name__)
    else:
        listings = Listing.objects.filter(state='A').order_by('-created_at')
        _include_highest_bid_listings(listings)
        return render(request, "auctions/index.html", {
            "listings": listings,
            "url_view": reverse("auctions:index")
        })


def all_listings(request):
    if request.method == "POST":
        return _add_remove_from_watchlist(request, all_listings.__name__)
    else:
        cat = request.GET.get('cat', '')
        listings = []
        if cat:
            if not cat.isdigit():
                if cat.lower() != 'none':
                    return HttpResponseRedirect(reverse("auctions:all_listings"))
                else:
                    listings = Listing.objects.filter(category__isnull=True)
            else:
                listings = Listing.objects.filter(category=cat)
        else:
            listings = Listing.objects.all()
        listings = listings.order_by('state', '-created_at')
        _include_highest_bid_listings(listings)
        categories = Category.objects.all()
        return render(request, "auctions/all_listings.html", {
            "listings": listings,
            "categories": categories,
            "url_view": reverse("auctions:all_listings")
        })


@login_required()
def my_listings(request):
    if request.method == "POST":
        return _add_remove_from_watchlist(request, my_listings.__name__)
    else:
        listings = Listing.objects.filter(
            user=request.user).order_by('-created_at')
        _include_highest_bid_listings(listings)
        return render(request, "auctions/my_listings.html", {
            "listings": listings,
            "url_view": reverse("auctions:my_listings")
        })


@login_required()
def watchlist(request):
    if request.method == "POST":
        return _add_remove_from_watchlist(request, watchlist.__name__)
    else:
        listings = Listing.objects.filter(
            user_watchlist=request.user).order_by('state', '-created_at')
        _include_highest_bid_listings(listings)
        return render(request, "auctions/watchlist.html", {
            "listings": listings,
            "url_view": reverse("auctions:watchlist")
        })


def _include_highest_bid_listings(listings):
    for l in listings:
        l.highest_bid = _get_highest_bid(l)[0]


def _get_highest_bid(l):
    all_bids = l.bid_listing.all()
    return (max(all_bids, key=lambda x: x.price) if all_bids else None, all_bids.count())


def _add_remove_from_watchlist(request, view):
    if 'btn_remove_watchlist' in request.POST or \
            'btn_add_watchlist' in request.POST:
        _add_remove_from_watchlist_helper(request, request.POST["listing_id"])
    return HttpResponseRedirect(reverse(f"auctions:{view}"))


def _add_remove_from_watchlist_helper(request, listing_id):
    try:
        listing = Listing.objects.get(pk=listing_id)
        user = request.user
    except KeyError:
        return HttpResponseBadRequest("Bad Request: no listing chosen")
    except Listing.DoesNotExist:
        return HttpResponseBadRequest("Bad Request: listing does not exist")
    except User.DoesNotExist:
        return HttpResponseBadRequest("Bad Request: user does not exist")
    if 'btn_remove_watchlist' in request.POST:
        user.watchlist.remove(listing)
    elif 'btn_add_watchlist' in request.POST:
        user.watchlist.add(listing)


@ login_required()
def new_listing(request):
    if request.method == "POST":
        try:
            category_request = request.POST['category']
            image_request = request.POST['image_url']
            new_listing = Listing(
                title=request.POST['title'],
                description=request.POST['description'],
                category=(Category.objects.get(
                    pk=category_request) if category_request else None),
                starting_price=Decimal(request.POST['starting_price']),
                image_url=(image_request if image_request else None),
                user=request.user)
            new_listing.save()
            return HttpResponseRedirect(reverse("auctions:my_listings"))
        except:
            return HttpResponseBadRequest("Bad Request")
    else:
        categories = Category.objects.all()
        return render(request, "auctions/new_listing.html", {
            "categories": categories
        })


def listing_page(request, listing_id):
    try:
        listing = Listing.objects.get(pk=listing_id)
        listing.highest_bid, listing.total_bids = _get_highest_bid(listing)
        comment_list = listing.comment_listing.all().order_by('-created_at')
        if request.method == "POST":
            if 'btn_remove_watchlist' in request.POST or \
                    'btn_add_watchlist' in request.POST:
                _add_remove_from_watchlist_helper(request, listing_id)
                return redirect("auctions:listing_page", listing_id=listing_id)
            elif 'btn_post_comment' in request.POST:
                textarea_form = TextAreaForm(
                    request.POST, error_class=DivErrorList)
                if textarea_form.is_valid():
                    content = textarea_form.cleaned_data["content"]
                    comment = Comment(
                        listing=listing, user=request.user, content=content)
                    comment.save()
                    return redirect("auctions:listing_page", listing_id=listing_id)
                else:
                    return render(request, "auctions/listing.html", {
                        "listing": listing,
                        "textarea_form": textarea_form,
                        "input_form": InputForm(),
                        "comments": comment_list
                    })
            elif 'btn_place_bid' in request.POST:
                input_form = InputForm(request.POST, error_class=DivErrorList)
                if input_form.is_valid():
                    bid_price = input_form.cleaned_data["bid_price"]
                    current_price = listing.highest_bid.price if listing.highest_bid else listing.starting_price
                    if current_price >= Decimal(bid_price):
                        return render(request, "auctions/listing.html", {
                            "listing": listing,
                            "input_form": input_form,
                            "textarea_form": TextAreaForm(),
                            "input_message": "Your bid has to be higher than the current price!",
                            "comments": comment_list
                        })
                    else:
                        bid = Bid(listing=listing, user=request.user,
                                  price=bid_price)
                        bid.save()
                else:
                    return render(request, "auctions/listing.html", {
                        "listing": listing,
                        "input_form": input_form,
                        "textarea_form": TextAreaForm(),
                        "comments": comment_list
                    })
            elif 'btn_close_auction' in request.POST:
                listing.state = 'C'
                listing.save(update_fields=['state'])
            return redirect("auctions:listing_page", listing_id=listing_id)
        else:
            return render(request, "auctions/listing.html", {
                "listing": listing,
                "input_form": InputForm(),
                "textarea_form": TextAreaForm(),
                "comments": comment_list
            })
    except KeyError:
        return HttpResponseBadRequest("Bad Request: no listing chosen")
    except Listing.DoesNotExist:
        return render(request, "auctions/listing.html", {
            "listing": None,
        })


def login_view(request):
    if request.method == "POST":

        # Attempt to sign user in
        username = request.POST["username"]
        password = request.POST["password"]
        user = authenticate(request, username=username, password=password)

        # Check if authentication successful
        if user is not None:
            login(request, user)
            next_param = request.POST.get('next', '')
            redirect_to = next_param if next_param else reverse(
                "auctions:index")
            return HttpResponseRedirect(redirect_to)
        else:
            return render(request, "auctions/login.html", {
                "message": "Invalid username and/or password."
            })
    else:
        return render(request, "auctions/login.html")


def logout_view(request):
    logout(request)
    return HttpResponseRedirect(reverse("auctions:index"))


def register(request):
    if request.method == "POST":
        first_name = request.POST["first_name"]
        last_name = request.POST["last_name"]

        username = request.POST["username"]
        email = request.POST["email"]

        # Ensure password matches confirmation
        password = request.POST["password"]
        confirmation = request.POST["confirmation"]
        if password != confirmation:
            return render(request, "auctions/register.html", {
                "message": "Passwords must match."
            })

        # Attempt to create new user
        try:
            user = User.objects.create_user(
                username, email, password, first_name=first_name, last_name=last_name)
            user.save()
        except IntegrityError:
            return render(request, "auctions/register.html", {
                "message": "Username already taken."
            })
        login(request, user)
        return HttpResponseRedirect(reverse("auctions:index"))
    else:
        return render(request, "auctions/register.html")
