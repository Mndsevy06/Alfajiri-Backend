from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.utils.translation import gettext_lazy as _

class CustomUserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError(_('The Email must be set'))
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)
        extra_fields.setdefault('role', 'Super Admin')

        if extra_fields.get('is_staff') is not True:
            raise ValueError(_('Superuser must have is_staff=True.'))
        if extra_fields.get('is_superuser') is not True:
            raise ValueError(_('Superuser must have is_superuser=True.'))
        return self.create_user(email, password, **extra_fields)

class User(AbstractUser):
    class Role(models.TextChoices):
        AGENT = 'Agent', 'Agent'
        COMPTABLE = 'Comptable', 'Comptable'
        CHEF_COMPTABLE = 'Chef Comptable', 'Chef Comptable'
        DIRECTEUR = 'Directeur', 'Directeur'
        AUDITEUR = 'Auditeur', 'Auditeur'
        SUPER_ADMIN = 'Super Admin', 'Super Admin'

    username = None
    email = models.EmailField(_('email address'), unique=True)
    role = models.CharField(
        max_length=50,
        choices=Role.choices,
        default=Role.AGENT,
    )
    nom = models.CharField(max_length=255, blank=True, null=True)
    site = models.CharField(max_length=100, blank=True, null=True)
    photo_profil = models.ImageField(upload_to='profiles/', null=True, blank=True)
    dossiers = models.ManyToManyField(
        'parametres.Dossier',
        blank=True,
        related_name='utilisateurs',
        verbose_name=_('Dossiers assignés')
    )
    preferences = models.JSONField(default=dict, blank=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    objects = CustomUserManager()

    def __str__(self):
        return f"{self.email} ({self.role})"

class RolePermission(models.Model):
    role = models.CharField(max_length=50, choices=User.Role.choices, unique=True)
    permissions = models.JSONField(default=dict)

    def __str__(self):
        return f"Permissions pour {self.role}"
