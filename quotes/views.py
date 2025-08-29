from django.shortcuts import render, redirect
from django.contrib import messages
from django.db.models import F
from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.http import require_POST
from django.views.decorators.cache import cache_page
from .models import Quote
from .utils import choose_weighted_quote
from .models import Source
from .forms import AddQuoteForm
from django.db.models import Sum, Avg, Count
from django.utils import timezone
from datetime import timedelta


def add_quote(request):
    if request.method == "POST":
        form = AddQuoteForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Цитата успешно добавлена!")
            return redirect("add_quote")  
        else:
            messages.error(request, "Исправьте ошибки в форме.")
    else:
        form = AddQuoteForm()

    return render(request, "quotes/add_quote.html", {"form": form})

def random_quote_view(request):
    qid = request.GET.get("qid")

    if qid:  # Если цитата выбрана явно через qid
        quote = get_object_or_404(Quote.objects.select_related("source"), pk=qid)
        increment_view = False
    else:  # При открытии случайной цитаты
        from .utils import choose_weighted_quote
        quote = choose_weighted_quote()
        increment_view = True

    if not quote:
        return render(request, "quotes/random.html", {"quote": None})

    if increment_view:
        Quote.objects.filter(pk=quote.pk).update(views=F("views") + 1)
        quote.views += 1

    

    vote_type = request.session.get(f"voted_{quote.pk}", None)
    return render(request, "quotes/random.html", {"quote": quote, "vote_type": vote_type})



@require_POST
def like_quote(request, quote_id: int):
    quote = get_object_or_404(Quote, pk=quote_id)
    key = f"voted_{quote_id}"

    prev_vote = request.session.get(key)

    if prev_vote == "like":
        # убрать лайк
        Quote.objects.filter(pk=quote_id).update(likes=F("likes") - 1)
        del request.session[key]
    elif prev_vote == "dislike":
        # заменить дизлайк на лайк
        Quote.objects.filter(pk=quote_id).update(
            dislikes=F("dislikes") - 1,
            likes=F("likes") + 1
        )
        request.session[key] = "like"
    else:
        # новый лайк
        Quote.objects.filter(pk=quote_id).update(likes=F("likes") + 1)
        request.session[key] = "like"

    return redirect(f"/?qid={quote_id}")


@require_POST
def dislike_quote(request, quote_id: int):
    quote = get_object_or_404(Quote, pk=quote_id)
    key = f"voted_{quote_id}"

    prev_vote = request.session.get(key)

    if prev_vote == "dislike":
        # убрать дизлайк
        Quote.objects.filter(pk=quote_id).update(dislikes=F("dislikes") - 1)
        del request.session[key]
    elif prev_vote == "like":
        # заменить лайк на дизлайк
        Quote.objects.filter(pk=quote_id).update(
            likes=F("likes") - 1,
            dislikes=F("dislikes") + 1
        )
        request.session[key] = "dislike"
    else:
        # новый дизлайк
        Quote.objects.filter(pk=quote_id).update(dislikes=F("dislikes") + 1)
        request.session[key] = "dislike"

    return redirect(f"/?qid={quote_id}")

@cache_page(30) # Кэширование топа на 30 секунд
def top_quotes(request):
    sort = request.GET.get("sort", "likes")
    period = request.GET.get("period", "all")
    source_id = request.GET.get("source")

    qs = Quote.objects.select_related("source").all()

    # Фильтр по периоду
    if period in ("7", "30"):
        days = int(period)
        since = timezone.now() - timedelta(days=days)
        qs = qs.filter(created_at__gte=since)

    # Фильтр по источнику
    if source_id:
        try:
            source_id = int(source_id)
            qs = qs.filter(source_id=source_id)
        except ValueError:
            pass

    # Словарь сортировок
    sort_map = {
        "likes": "-likes",
        "views": "-views",
        "dislikes": "-dislikes",
        "weight": "-weight",
        "recent": "-created_at",
    }
    order_field = sort_map.get(sort, "-likes")
    qs = qs.order_by(order_field)

    top_list = qs[:10]  # топ 10

    sources = Source.objects.order_by("name").all()

    context = {
        "top_list": top_list,
        "sources": sources,
        "selected_sort": sort,
        "selected_period": period,
        "selected_source": source_id,
    }
    return render(request, "quotes/top.html", context)


def dashboard(request):
    total_quotes = Quote.objects.count()
    total_likes = Quote.objects.aggregate(total=Sum("likes"))["total"] or 0
    total_dislikes = Quote.objects.aggregate(total=Sum("dislikes"))["total"] or 0
    total_views = Quote.objects.aggregate(total=Sum("views"))["total"] or 0
    avg_weight = Quote.objects.aggregate(avg=Avg("weight"))["avg"] or 0

    # Топ источников по сумме лайков их цитат
    top_sources = (
        Source.objects
        .annotate(num_quotes=Count("quotes"), sum_likes=Sum("quotes__likes"))
        .order_by("-sum_likes")[:10]
    )

    context = {
        "total_quotes": total_quotes,
        "total_likes": total_likes,
        "total_dislikes": total_dislikes,
        "total_views": total_views,
        "avg_weight": round(avg_weight, 2) if avg_weight else 0,
        "top_sources": top_sources,
    }
    return render(request, "quotes/dashboard.html", context)