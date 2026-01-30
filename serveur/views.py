from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q
from django.core.mail import send_mail
from django.db.models import Q
from django.shortcuts import render
from django.contrib.auth.decorators import login_required

from django.conf import settings

from .models import (
    Category,
    Licence,
    ServiceImei,
    Wallet,
    Transaction,
    Commande,
    Historique,
    PaymentConfig,
    CommandeFieldValue,
    Service,
)

# =====================================================
# PAGE D’ACCUEIL PUBLIQUE (AVANT CONNEXION)
# =====================================================


def home(request):
    # si connecté → accueil privé
    if request.user.is_authenticated:
        return redirect("accueil")

    query = request.GET.get("q", "").strip()

    categories = Category.objects.prefetch_related(
    "licences",
    "services",              # ServiceImei
    "services_generaux"      # Service
)

    if query:
        categories = categories.filter(
            Q(licences__nom__icontains=query) |
            Q(licences__destription__icontains=query) |
            Q(services__nom__icontains=query) |
            Q(services__destription__icontains=query)
        ).distinct()

    return render(request, "affirche/home.html", {
        "categories": categories,
        "query": query,
    })



# =====================================================
# ACCUEIL PRIVÉ (APRÈS CONNEXION) – DYNAMIQUE PAR CATÉGORIE
# =====================================================

@login_required
def accueil(request):
    query = request.GET.get("q", "").strip()

    categories = Category.objects.prefetch_related(
        "licences",
        "services",
        "services_generaux",
    )

    if query:
        categories = categories.filter(
            Q(nom__icontains=query) |
            Q(licences__nom__icontains=query) |
            Q(licences__destription__icontains=query) |
            Q(services__nom__icontains=query) |
            Q(services__destription__icontains=query) |
            Q(services_generaux__nom__icontains=query) |
            Q(services_generaux__description__icontains=query)
        ).distinct()

    commandes = Commande.objects.filter(
        user=request.user
    ).order_by("-date")

    historiques = Historique.objects.filter(
        user=request.user
    ).order_by("-date")

    wallet, _ = Wallet.objects.get_or_create(user=request.user)

    context = {
        "categories": categories,
        "commandes": commandes,
        "historiques": historiques,
        "wallet": wallet,
        "query": query,
    }

    return render(request, "affirche/accueil.html", context)



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
    print("🚨 ajouter_fonds APPELÉ 🚨")

    if request.method != "POST":
        print("❌ PAS UN POST")
        return redirect("fonds")

    print("✅ POST DÉTECTÉ")

    montant = request.POST.get("montant")
    methode = request.POST.get("methode")
    reference = request.POST.get("reference")

    print("📦 DONNÉES :", montant, methode, reference)

    if not montant or not methode or not reference:
        print("❌ CHAMPS MANQUANTS")
        messages.error(request, "Tous les champs sont obligatoires.")
        return redirect("fonds")

    transaction = Transaction.objects.create(
        user=request.user,
        montant=int(montant),
        methode=methode,
        reference=reference,
        statut="attente"
    )

    print("✅ TRANSACTION CRÉÉE")

    config = PaymentConfig.objects.filter(
        methode=methode,
        actif=True
    ).first()

    numero = config.numero if config else "NON DÉFINI"

    print("📧 AVANT SEND_MAIL")

    send_mail(
        subject="💰 Nouvelle demande d'ajout de fonds",
        message=(
            f"Utilisateur : {request.user.username}\n"
            f"Email : {request.user.email}\n"
            f"Méthode : {methode}\n"
            f"Numéro : {numero}\n"
            f"Montant : {montant} FCFA\n"
            f"Référence : {reference}"
        ),
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[settings.ADMIN_EMAIL],
        fail_silently=False,
    )

    print("✅ APRÈS SEND_MAIL")

    messages.success(request, "Demande envoyée. En attente de validation.")
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
# COMMANDE (LICENCE / SERVICE)
# =====================================================
@login_required
def commande(request, type_produit, produit_id):

    # =========================
    # RÉCUPÉRATION PRODUIT
    # =========================
    if type_produit == "licence":
        produit = get_object_or_404(Licence, id=produit_id)
        produit.need_email = True
        produit.need_username = True
        produit.need_imei = False
        produit.need_photo = False

    elif type_produit == "service":
        produit = get_object_or_404(ServiceImei, id=produit_id)
        produit.need_email = True
        produit.need_username = True
        produit.need_imei = True
        produit.need_photo = False

    elif type_produit == "service_general":
        produit = get_object_or_404(Service, id=produit_id)
        produit.need_email = produit.demande_email
        produit.need_username = produit.demande_username
        produit.need_imei = produit.demande_imei
        produit.need_photo = produit.demande_photo

    else:
        messages.error(request, "Produit invalide")
        return redirect("accueil")

    # =========================
    # CHAMPS DYNAMIQUES
    # =========================
    custom_fields = []

    if hasattr(produit, "custom_fields"):
        custom_fields.extend(produit.custom_fields.all())

    if produit.category:
        for field in produit.category.custom_fields.all():
            if field not in custom_fields:
                custom_fields.append(field)

    # =========================
    # POST
    # =========================
    if request.method == "POST":

        commande = Commande.objects.create(
            user=request.user,
            type_commande=type_produit,
            nom_produit=produit.nom,
            prix=produit.prix,
            email=request.POST.get("email", ""),
            username_service=request.POST.get("username_service", ""),
            imei=request.POST.get("imei", ""),
            photo_lien=request.POST.get("photo_lien", ""),
            statut="attente"
        )

        # =========================
        # SAUVEGARDE CHAMPS CUSTOM
        # =========================
        custom_text = ""
        for field in custom_fields:
            value = request.POST.get(f"custom_{field.id}")
            if value:
                CommandeFieldValue.objects.create(
                    commande=commande,
                    field=field,
                    value=value
                )
                custom_text += f"{field.nom} : {value}\n"

        # =========================
        # EMAIL ADMIN (ICI ✅)
        # =========================
        send_mail(
            subject="🛒 Nouvelle commande - SK Serveur",
            message=(
                f"Utilisateur : {request.user.username}\n"
                f"Email compte : {request.user.email}\n\n"
                f"Produit : {commande.nom_produit}\n"
                f"Type : {type_produit}\n"
                f"Prix : {commande.prix} FCFA\n\n"
                f"--- INFOS COMMANDE ---\n"
                f"Email service : {commande.email}\n"
                f"Username : {commande.username_service}\n"
                f"IMEI : {commande.imei}\n"
                f"Photo : {commande.photo_lien}\n\n"
                f"--- CHAMPS PERSONNALISÉS ---\n"
                f"{custom_text}"
            ),
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[settings.ADMIN_EMAIL],
            fail_silently=False,
        )

        messages.success(request, "Commande envoyée avec succès")
        return redirect("accueil")

    # =========================
    # GET
    # =========================
    return render(request, "affirche/commande.html", {
        "produit": produit,
        "custom_fields": custom_fields
    })

    # =========================
    # CHAMPS DYNAMIQUES
    # =========================
    custom_fields = getattr(produit, "custom_fields", []).all() if hasattr(produit, "custom_fields") else []

    # =========================
    # POST
    # =========================
    if request.method == "POST":

        email = request.POST.get("email")
        username_service = request.POST.get("username_service")
        imei = request.POST.get("imei")
        photo_lien = request.POST.get("photo_lien")

        # validation dynamique
        if produit.need_email and not email:
            messages.error(request, "Email obligatoire.")
            return redirect(request.path)

        if produit.need_username and not username_service:
            messages.error(request, "Nom d'utilisateur obligatoire.")
            return redirect(request.path)

        if produit.need_imei and not imei:
            messages.error(request, "IMEI obligatoire.")
            return redirect(request.path)

        if produit.need_photo and not photo_lien:
            messages.error(request, "Photo obligatoire.")
            return redirect(request.path)

        if wallet.solde < produit.prix:
            messages.error(request, "Solde insuffisant.")
            return redirect("fonds")

        wallet.solde -= produit.prix
        wallet.save()

        # ✅ CRÉATION COMMANDE (STOCKÉE)
        commande = Commande.objects.create(
            user=request.user,
            type_commande=type_produit,
            nom_produit=produit.nom,
            prix=produit.prix,
            email=email or "",
            username_service=username_service or "",
            imei=imei,
            photo_lien=photo_lien,
            statut="attente"
        )

        # =========================
        # VALEURS DES CHAMPS CUSTOM
        # =========================
        for field in custom_fields:
            value = request.POST.get(f"custom_{field.id}")
            if value:
                CommandeFieldValue.objects.create(
                    commande=commande,
                    field=field,
                    value=value
                )

        send_mail(
            subject="🛒 Nouvelle commande reçue",
            message=(
                f"Utilisateur : {request.user.username}\n"
                f"Produit : {produit.nom}\n"
                f"Prix : {produit.prix} FCFA\n"
            ),
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[settings.ADMIN_EMAIL],
            fail_silently=False,
        )

        messages.success(request, "Commande envoyée (en attente de validation).")
        return redirect("accueil")

    # =========================
    # GET
    # =========================
    return render(request, "affirche/commande.html", {
        "produit": produit,
        "type": type_produit,
        "custom_fields": custom_fields,
    })


