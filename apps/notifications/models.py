import uuid
from django.db import models
from django.conf import settings


class Notification(models.Model):
    class Type(models.TextChoices):
        CRITICAL = 'critical', 'Critique'
        URGENT   = 'urgent',   'Urgente'
        WARNING  = 'warning',  'Avertissement'
        INFO     = 'info',     'Information'

    class Module(models.TextChoices):
        COMPTABILITE  = 'comptabilite',  'Comptabilité'
        VENTES        = 'ventes',        'Ventes & Facturation'
        PAIEMENTS     = 'paiements',     'Paiements & Trésorerie'
        LOGISTIQUE    = 'logistique',    'Logistique'
        TERRAIN       = 'terrain',       'Terrain'
        RH            = 'rh',            'Ressources Humaines'
        FISCALITE     = 'fiscalite',     'Fiscalité'
        RAPPROCHEMENT = 'rapprochement', 'Rapprochement Bancaire'
        IMMOBILISATIONS = 'immobilisations', 'Immobilisations'
        CLOTURE       = 'cloture',       'Clôture & États Financiers'
        SECURITE      = 'securite',      'Sécurité & Système'

    id         = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    # null = notification broadcast globale
    user       = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        null=True, blank=True,
        related_name='notifications'
    )
    dossier    = models.ForeignKey(
        'parametres.Dossier',
        on_delete=models.CASCADE,
        null=True, blank=True,
        related_name='notifications'
    )
    titre      = models.CharField(max_length=255)
    message    = models.TextField()
    type       = models.CharField(max_length=20, choices=Type.choices, default=Type.INFO)
    module     = models.CharField(max_length=50, choices=Module.choices, default=Module.SECURITE)
    action_url = models.CharField(max_length=255, blank=True, null=True)
    lu         = models.BooleanField(default=False)
    cree_le    = models.DateTimeField(auto_now_add=True)
    meta       = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering = ['-cree_le']
        verbose_name = 'Notification'
        verbose_name_plural = 'Notifications'

    def __str__(self):
        target = self.user.email if self.user else 'broadcast'
        return f'[{self.type}] {self.titre} → {target}'
