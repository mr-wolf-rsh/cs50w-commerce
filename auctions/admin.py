from django.contrib import admin
from .models import Category, Listing, Bid, Comment, User

# Register your models here.


@admin.register(Category, Bid, Comment)
class UniversalAdmin(admin.ModelAdmin):
    def get_list_display(self, request):
        return [field.name for field in self.model._meta.concrete_fields]


class ListingAdmin(admin.ModelAdmin):
    list_display = [
        field.name for field in Listing._meta.concrete_fields if field.name != 'description']


admin.site.register(Listing, ListingAdmin)


class UserAdmin(admin.ModelAdmin):
    list_display = [
        field.name for field in User._meta.concrete_fields if field.name != 'password']
    filter_horizontal = ("watchlist",)


admin.site.register(User, UserAdmin)
