from django.urls import path
from . import views

urlpatterns = [
    path("add/", views.add_quote, name="add_quote"),
    path("", views.random_quote_view, name="home"),
    path("like/<int:quote_id>/", views.like_quote, name="like_quote"),
    path("dislike/<int:quote_id>/", views.dislike_quote, name="dislike_quote"),
    path("top/", views.top_quotes, name="top_quotes"),
    path("dashboard/", views.dashboard, name="dashboard"),
]
