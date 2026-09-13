from django.contrib import admin

from .models import Conversation, Deal, Message, Offer


admin.site.register(Conversation)
admin.site.register(Message)
admin.site.register(Offer)
admin.site.register(Deal)
