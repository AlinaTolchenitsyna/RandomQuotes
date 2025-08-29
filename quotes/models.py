from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models


class Source(models.Model):
    class Kind(models.TextChoices):
        MOVIE = "movie", "Фильм"
        BOOK = "book", "Книга"
        SERIES = "series", "Сериал"
        OTHER = "other", "Другое"

    name = models.CharField("Название источника", max_length=255, unique=True, db_index=True)
    kind = models.CharField("Тип", max_length=16, choices=Kind.choices, default=Kind.OTHER)
    extra = models.CharField("Автор/режиссёр/прочее", max_length=255, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["name"]
        verbose_name = "Источник"
        verbose_name_plural = "Источники"

    def __str__(self) -> str:
        return f"{self.name} ({self.get_kind_display()})"


class Quote(models.Model):
    text = models.TextField("Текст цитаты", unique=True)
    source = models.ForeignKey(Source, on_delete=models.CASCADE, related_name="quotes", verbose_name="Источник")

    weight = models.PositiveIntegerField("Вес (≥1)", default=1, validators=[MinValueValidator(1)])

    likes = models.PositiveIntegerField("Лайки", default=0)
    dislikes = models.PositiveIntegerField("Дизлайки", default=0)
    views = models.PositiveIntegerField("Просмотры", default=0)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Цитата"
        verbose_name_plural = "Цитаты"

    def clean(self):
        # Обрезка пробелов, чтобы они не учитывались при уникальности
        if self.text:
            self.text = self.text.strip()

        if self.source_id:
            # Подсчет цитат у источника (должно быть не больше 3), за исключением текущей (если она редактируется, а не добавляется)
            existing_count = Quote.objects.filter(source_id=self.source_id).exclude(pk=self.pk).count()
            if existing_count >= 3:
                raise ValidationError({"source": "У этого источника уже есть 3 цитаты. Нельзя добавить больше."})

    def save(self, *args, **kwargs):
        self.full_clean() # валидация на уровне Django
        return super().save(*args, **kwargs)

    def __str__(self) -> str:
        return f"{self.text[:60]}{'…' if len(self.text) > 60 else ''}" # В списках цитата отображается как первые 60 символов + многоточие
