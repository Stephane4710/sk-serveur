from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    # PAGE PUBLIQUE
    path("", views.home, name="home"),

    # AUTH
    path("login/", views.login_view, name="login"),
    path("register/", views.register_view, name="register"),
    path("logout/", auth_views.LogoutView.as_view(next_page="home"), name="logout"),

    # PRIVÉ
    path("accueil/", views.accueil, name="accueil"),
    path("fonds/", views.fonds, name="fonds"),
    path("ajouter-fonds/", views.ajouter_fonds, name="ajouter_fonds"),

    # COMMANDE
    path(
        "commande/<str:type_produit>/<int:produit_id>/",
        views.commande,
        name="commande"
    ),
]
