import random
from typing import Optional
from .models import Quote

def choose_weighted_quote() -> Optional[Quote]:
    
    items = list(Quote.objects.values_list("id", "weight"))
    if not items:
        return None

    ids, weights = zip(*items)  
    chosen_id = random.choices(population=ids, weights=weights, k=1)[0]

    return Quote.objects.select_related("source").get(pk=chosen_id)
