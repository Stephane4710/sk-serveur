from django.contrib import admin, messages
from django.contrib.auth.models import User
from django.contrib.auth.admin import UserAdmin
from django.core.mail import send_mail
from django.conf import settings

from .models import (
    Licence,
    ServiceImei,
    Category,
    Historique,
    Wallet,
    Transaction,
    Commande,
    PaymentConfig,
)

# =========================
# CATEGORY
# =========================
@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("nom", "date_ajout")


# =========================
# LICENCE
# =========================
@admin.register(Licence)
class LicenceAdmin(admin.ModelAdmin):
    list_display = ("nom", "prix", "category", "date_ajout")
    list_editable = ("prix",)


# =========================
# SERVICE IMEI
# =========================
@admin.register(ServiceImei)
class ServiceImeiAdmin(admin.ModelAdmin):
    list_display = ("nom", "prix", "category", "date_ajout")
    list_editable = ("prix",)


# =========================
# HISTORIQUE (LECTURE SEULE)
# =========================
@admin.register(Historique)
class HistoriqueAdmin(admin.ModelAdmin):
    list_display = ("user", "nom_service", "prix", "statut", "date")
    readonly_fields = ("user", "nom_service", "prix", "statut", "date")


# =========================
# WALLET
# =========================
@admin.register(Wallet)
class WalletAdmin(admin.ModelAdmin):
    list_display = ("user", "solde")
    readonly_fields = ("user",)


# =========================
# ACTION : VALIDER COMMANDE
# =========================
def valider_commande(modeladmin, request, queryset):
    count = 0
    for c in queryset:
        if c.statut == "attente":
            c.statut = "succes"
            c.save()

            Historique.objects.create(
                user=c.user,
                nom_service=c.nom_produit,
                prix=c.prix,
                statut="succes",
            )

            # 📧 EMAIL UTILISATEUR
            send_mail(
                subject="✅ Commande validée - SK Serveur",
                message=(
                    f"Bonjour {c.user.username},\n\n"
                    f"Votre commande '{c.nom_produit}' a été VALIDÉE avec succès.\n"
                    f"Montant : {c.prix} FCFA\n\n"
                    f"Merci pour votre confiance.\n"
                    f"— SK Serveur"
                ),
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[c.user.email],
                fail_silently=True,
            )

            count += 1

    messages.success(request, f"{count} commande(s) validée(s).")


# =========================
# ACTION : REFUSER COMMANDE
# =========================
def refuser_commande(modeladmin, request, queryset):
    count = 0
    for c in queryset:
        if c.statut == "attente":
            c.statut = "refuse"
            c.save()

            # 💰 remboursement
            wallet, _ = Wallet.objects.get_or_create(user=c.user)
            wallet.solde += c.prix
            wallet.save()

            Historique.objects.create(
                user=c.user,
                nom_service=c.nom_produit,
                prix=c.prix,
                statut="echec",
            )

            # 📧 EMAIL UTILISATEUR
            send_mail(
                subject="❌ Commande refusée - SK Serveur",
                message=(
                    f"Bonjour {c.user.username},\n\n"
                    f"Votre commande '{c.nom_produit}' a été REFUSÉE.\n"
                    f"Le montant de {c.prix} FCFA a été remboursé dans votre solde.\n\n"
                    f"— SK Serveur"
                ),
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[c.user.email],
                fail_silently=True,
            )

            count += 1

    messages.warning(
        request,
        f"{count} commande(s) refusée(s) et remboursée(s)."
    )


# =========================
# COMMANDE
# =========================
@admin.register(Commande)
class CommandeAdmin(admin.ModelAdmin):
    list_display = ("user", "nom_produit", "prix", "statut", "date")
    list_filter = ("statut",)
    readonly_fields = ("user", "nom_produit", "prix", "date")
    actions = [valider_commande, refuser_commande]


# =========================
# PAYMENT CONFIG
# =========================
@admin.register(PaymentConfig)
class PaymentConfigAdmin(admin.ModelAdmin):
    list_display = ("methode", "numero", "actif")
    list_editable = ("numero", "actif")


# =========================
# USERS
# =========================
class CustomUserAdmin(UserAdmin):
    pass


# =========================
# ACTION : VALIDER TRANSACTION (RECHARGE)
# =========================
def valider_transaction(modeladmin, request, queryset):
    count = 0
    for t in queryset:
        if t.statut == "attente":
            t.statut = "valide"
            t.save()

            wallet, _ = Wallet.objects.get_or_create(user=t.user)
            wallet.solde += t.montant
            wallet.save()

            count += 1

    messages.success(
        request,
        f"{count} recharge(s) validée(s) et solde crédité."
    )


# =========================
# ACTION : REFUSER TRANSACTION
# =========================
def refuser_transaction(modeladmin, request, queryset):
    count = 0
    for t in queryset:
        if t.statut == "attente":
            t.statut = "refuse"
            t.save()
            count += 1

    messages.warning(
        request,
        f"{count} recharge(s) refusée(s)."
    )


# =========================
# TRANSACTION (ADMIN)
# =========================
@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ("user", "montant", "methode", "reference", "statut", "date")
    list_filter = ("statut", "methode")
    readonly_fields = ("user", "montant", "methode", "reference", "date")
    actions = [valider_transaction, refuser_transaction]



admin.site.unregister(User)
admin.site.register(User, CustomUserAdmin)
