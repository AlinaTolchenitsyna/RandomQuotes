from django import forms
from .models import Quote


class AddQuoteForm(forms.ModelForm):
    class Meta:
        model = Quote
        fields = ["text", "source", "weight"]

    def clean(self):
        cleaned_data = super().clean()
        source = cleaned_data.get("source")

        if source:
            if source.quotes.count() >= 3:
                raise forms.ValidationError(
                    "У этого источника уже есть 3 цитаты. Нельзя добавить больше."
                )
        return cleaned_data
