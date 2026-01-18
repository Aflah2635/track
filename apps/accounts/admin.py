from django.contrib import admin
from .models import Account, AccountAccess

admin.site.register(Account)
admin.site.register(AccountAccess)
