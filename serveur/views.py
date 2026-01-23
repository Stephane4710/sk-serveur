from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q
from django.core.mail import send_mail
from django.conf import settings


from .models import (
    Licence,
    ServiceImei,
    Wallet,
    Transaction,
    Commande,
    Historique,
    PaymentConfig,
)

# =====================================================
# PAGE D’ACCUEIL PUBLIQUE (AVANT CONNEXION)
# =====================================================
def home(request):
    # Si déjà connecté → accueil privé
    if request.user.is_authenticated:
        return redirect("accueil")

    query = request.GET.get("q", "").strip()

    licences = Licence.objects.all()
    services = ServiceImei.objects.all()

    if query:
        licences = Licence.objects.filter(
            Q(nom__icontains=query) |
            Q(destription__icontains=query)
        )
        services = ServiceImei.objects.filter(
            Q(nom__icontains=query) |
            Q(destription__icontains=query)
        )

    return render(request, "affirche/home.html", {
        "licences": licences,
        "services": services,
        "query": query,
    })


# =====================================================
# ACCUEIL PRIVÉ (APRÈS CONNEXION)
# =====================================================
@login_required
def accueil(request):
    query = request.GET.get("q", "").strip()

    licences = Licence.objects.all()
    services = ServiceImei.objects.all()

    if query:
        licences = Licence.objects.filter(
            Q(nom__icontains=query) |
            Q(destription__icontains=query)
        )
        services = ServiceImei.objects.filter(
            Q(nom__icontains=query) |
            Q(destription__icontains=query)
        )

    commandes_attente = Commande.objects.filter(
        user=request.user,
        statut="attente"
    ).order_by("-date")

    historiques = Historique.objects.filter(
        user=request.user
    ).order_by("-date")

    wallet, _ = Wallet.objects.get_or_create(user=request.user)

    return render(request, "affirche/accueil.html", {
        "licences": licences,
        "services": services,
        "commandes_attente": commandes_attente,
        "historiques": historiques,
        "wallet": wallet,
        "query": query,
    })


# =====================================================
# PAGE FONDS
# =====================================================
@login_required
def fonds(request):
    wallet, _ = Wallet.objects.get_or_create(user=request.user)

    transactions = Transaction.objects.filter(
        user=request.user
    ).order_by("-date")

    payment_configs = PaymentConfig.objects.filter(actif=True)

    return render(request, "affirche/fonds.html", {
        "wallet": wallet,
        "transactions": transactions,
        "payment_configs": payment_configs,
    })


# =====================================================
# AJOUTER DES FONDS
# =====================================================
@login_required
def ajouter_fonds(request):
    if request.method == "POST":
        montant = request.POST.get("montant")
        methode = request.POST.get("methode")
        reference = request.POST.get("reference")

        if not montant or not methode or not reference:
            messages.error(request, "Tous les champs sont obligatoires.")
            return redirect("fonds")

        Transaction.objects.create(
            user=request.user,
            montant=montant,
            methode=methode,
            reference=reference,
            statut="attente"
        )

        messages.success(request, "Demande envoyée. En attente de validation.")
        return redirect("fonds")

    return redirect("fonds")


# =====================================================
# AUTHENTIFICATION
# =====================================================
def login_view(request):
    if request.method == "POST":
        user = authenticate(
            request,
            username=request.POST.get("username"),
            password=request.POST.get("password")
        )
        if user:
            login(request, user)
            return redirect("accueil")

        messages.error(request, "Identifiants incorrects")

    return render(request, "affirche/login.html")


def register_view(request):
    if request.method == "POST":
        if request.POST["password1"] != request.POST["password2"]:
            messages.error(request, "Les mots de passe ne correspondent pas.")
            return redirect("register")

        if User.objects.filter(username=request.POST["username"]).exists():
            messages.error(request, "Nom d’utilisateur déjà utilisé.")
            return redirect("register")

        User.objects.create_user(
            username=request.POST["username"],
            email=request.POST["email"],
            password=request.POST["password1"]
        )

        messages.success(request, "Compte créé avec succès.")
        return redirect("login")

    return render(request, "affirche/register.html")


# =====================================================
# COMMANDE (LICENCE / SERVICE IMEI)
# =====================================================
@login_required


@login_required
def commande(request, type_produit, produit_id):

    if type_produit == "licence":
        produit = get_object_or_404(Licence, id=produit_id)
    elif type_produit == "service":
        produit = get_object_or_404(ServiceImei, id=produit_id)
    else:
        messages.error(request, "Type de produit invalide.")
        return redirect("accueil")

    wallet, _ = Wallet.objects.get_or_create(user=request.user)

    if request.method == "POST":
        email = request.POST.get("email")
        username_service = request.POST.get("username_service")

        if not email or not username_service:
            messages.error(request, "Tous les champs sont obligatoires.")
            return redirect(request.path)

        if wallet.solde < produit.prix:
            messages.error(request, "Solde insuffisant.")
            return redirect("fonds")

        # 💰 Débit
        wallet.solde -= produit.prix
        wallet.save()

        # 🛒 Création commande
        Commande.objects.create(
            user=request.user,
            type_commande=type_produit,
            nom_produit=produit.nom,
            prix=produit.prix,
            email=email,
            username_service=username_service,
            statut="attente"
        )

        # 📧 EMAIL À L’ADMIN
        send_mail(
            subject="🛒 Nouvelle commande reçue",
            message=(
                f"Nouvelle commande passée sur SK Serveur\n\n"
                f"Utilisateur : {request.user.username}\n"
                f"Email : {email}\n"
                f"Produit : {produit.nom}\n"
                f"Prix : {produit.prix} FCFA\n"
                f"Type : {type_produit}\n\n"
                f"Connecte-toi à l’admin pour la traiter."
            ),
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[settings.ADMIN_EMAIL],
            fail_silently=False,
)


        messages.success(request, "Commande envoyée (en attente de validation).")
        return redirect("accueil")

    return render(request, "affirche/commande.html", {
        "produit": produit,
        "type": type_produit
    })



