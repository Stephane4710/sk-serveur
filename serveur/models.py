from django.db import models
from django.contrib.auth.models import User


# =========================
# CATEGORY
# =========================
class Category(models.Model):
    nom = models.CharField(max_length=200)
    date_ajout = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-date_ajout']

    def __str__(self):
        return self.nom


# =========================
# LICENCE
# =========================
class Licence(models.Model):
    nom = models.CharField(max_length=200)
    prix = models.PositiveIntegerField()
    category = models.ForeignKey(Category, related_name='licences', on_delete=models.CASCADE)
    destription = models.TextField()
    image = models.URLField(max_length=5000, blank=True)
    need_email = models.BooleanField(default=True)
    need_username = models.BooleanField(default=True)
    need_imei = models.BooleanField(default=False)
    need_photo = models.BooleanField(default=False)

    date_ajout = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.nom


# =========================
# SERVICE IMEI
# =========================
class ServiceImei(models.Model):
    nom = models.CharField(max_length=200)
    prix = models.PositiveIntegerField()
    category = models.ForeignKey(Category, related_name='services', on_delete=models.CASCADE)
    destription = models.TextField()
    need_email = models.BooleanField(default=True)
    need_username = models.BooleanField(default=True)
    need_imei = models.BooleanField(default=True)
    need_photo = models.BooleanField(default=True)

    date_ajout = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.nom


# =========================
# WALLET
# =========================
class Wallet(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    solde = models.PositiveIntegerField(default=0)

    def __str__(self):
        return f"{self.user.username} - {self.solde} FCFA"


# =========================
# TRANSACTION
# =========================
class Transaction(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    montant = models.PositiveIntegerField()

    methode = models.CharField(
        max_length=20,
        choices=[
            ('wave', 'Wave'),
            ('mtn', 'MTN Money'),
            ('orange', 'Orange Money'),
        ]
    )

    reference = models.CharField(max_length=100)

    statut = models.CharField(
        max_length=20,
        choices=[
            ('attente', 'En attente'),
            ('valide', 'Validée'),
            ('refuse', 'Refusée'),
        ],
        default='attente'
    )

    date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.montant} FCFA"


# =========================
# COMMANDE (CYCLE DE VIE)
# =========================
class Commande(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)

    TYPE_CHOIX = [
        ('licence', 'Licence'),
        ('service', 'Service IMEI'),
    ]

    STATUT_CHOIX = [
        ('attente', 'En attente'),
        ('succes', 'Succès'),
        ('refuse', 'Refusée'),
    ]

    type_commande = models.CharField(max_length=20, choices=TYPE_CHOIX)
    nom_produit = models.CharField(max_length=200)
    prix = models.PositiveIntegerField()

    email = models.EmailField()
    username_service = models.CharField(max_length=150)

    # 🔐 Spécifique aux services IMEI
    imei = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        help_text="IMEI du téléphone (uniquement pour service IMEI)"
    )

    photo_lien = models.URLField(
        max_length=1000,
        blank=True,
        null=True,
        help_text="Lien de la photo du téléphone (hébergée en ligne)"
    )

    statut = models.CharField(
        max_length=20,
        choices=STATUT_CHOIX,
        default='attente'
    )

    date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.nom_produit} ({self.statut})"


# =========================
# HISTORIQUE (FINAL UNIQUEMENT)
# =========================
class Historique(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    nom_service = models.CharField(max_length=200)
    prix = models.PositiveIntegerField()

    statut = models.CharField(
        max_length=20,
        choices=[
            ('succes', 'Succès'),
            ('echec', 'Échec'),
        ]
    )

    date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.nom_service} - {self.statut}"
    


    # =========================
# CONFIGURATION PAIEMENT
# =========================
class PaymentConfig(models.Model):
    METHODE_CHOICES = [
        ('wave', 'Wave'),
        ('mtn', 'MTN Money'),
        ('orange', 'Orange Money'),
    ]

    methode = models.CharField(
        max_length=20,
        choices=METHODE_CHOICES,
        unique=True
    )

    numero = models.CharField(max_length=30)
    actif = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.methode.upper()} - {self.numero}"
    

    




# =========================
# CHAMPS DYNAMIQUES (ADMIN)
# =========================
from django.core.exceptions import ValidationError

class CustomField(models.Model):
    TYPE_CHOICES = [
        ("text", "Texte"),
        ("number", "Nombre"),
        ("email", "Email"),
        ("imei", "IMEI"),
        ("url", "Lien"),
    ]

    nom = models.CharField(max_length=100)
    type = models.CharField(max_length=20, choices=TYPE_CHOICES)
    obligatoire = models.BooleanField(default=True)

    # 🔥 LIÉ À LA CATÉGORIE (BONNE PRATIQUE)
    category = models.ForeignKey(
        Category,
        related_name="custom_fields",
        on_delete=models.CASCADE,
        null=True,
        blank = True
    )

    def __str__(self):
        return f"{self.nom} ({self.category.nom})"




    # champ lié à un service OU une licence
    licence = models.ForeignKey(
        Licence,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="custom_fields"
    )

    service = models.ForeignKey(
        "Service",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="custom_fields"
    )

    def __str__(self):
        return self.nom


# =========================
# VALEUR DES CHAMPS (COMMANDE)
# =========================
class CommandeFieldValue(models.Model):
    commande = models.ForeignKey(
        Commande,
        on_delete=models.CASCADE,
        related_name="field_values"
    )
    field = models.ForeignKey(CustomField, on_delete=models.CASCADE)
    value = models.TextField()

    def __str__(self):
        return f"{self.field.nom} : {self.value}"
    





class Service(models.Model):
    nom = models.CharField(max_length=200)
    prix = models.PositiveIntegerField()
    category = models.ForeignKey(
    Category,
    on_delete=models.CASCADE,
    related_name="services_generaux"
)

    description = models.TextField()
    image = models.URLField(blank=True, null=True)

    # options dynamiques
    demande_email = models.BooleanField(default=True)
    demande_username = models.BooleanField(default=True)
    demande_imei = models.BooleanField(default=False)
    demande_photo = models.BooleanField(default=False)

    date_ajout = models.DateTimeField(auto_now=True)
    

    def __str__(self):
        return self.nom




