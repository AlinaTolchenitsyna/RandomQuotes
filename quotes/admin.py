from django.contrib import admin
from django.forms import Textarea
from django.db import models

from .models import Source, Quote


@admin.register(Source)
class SourceAdmin(admin.ModelAdmin):
    list_display = ("name", "kind", "created_at")
    list_filter = ("kind",)
    search_fields = ("name", "extra")


@admin.register(Quote)
class QuoteAdmin(admin.ModelAdmin):
    list_display = ("short_text", "source", "weight", "likes", "dislikes", "views", "created_at")
    list_filter = ("source__kind", "source",)
    search_fields = ("text", "source__name")
    autocomplete_fields = ("source",)
    readonly_fields = ("likes", "dislikes", "views", "created_at", "updated_at")

    formfield_overrides = {
        models.TextField: {"widget": Textarea(attrs={"rows": 4, "cols": 80})},
    }

    def short_text(self, obj):
        return (obj.text[:60] + "…") if len(obj.text) > 60 else obj.text

    short_text.short_description = "Цитата"
