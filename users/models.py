from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager
from django.core.validators import validate_email
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from datetime import timedelta


class UserManager(BaseUserManager):
    def email_validator(self, email):
        try:
            validate_email(email)
        except ValidationError:
            raise ValueError(_("Please enter a valid email address."))

    def create_user(self, first_name, last_name, email, password, **extra_fields):
        if email:
            email = self.normalize_email(email)
            self.email_validator(email)
        else:
            raise ValueError(_("An email address is required."))
        if not first_name:
            raise ValueError(_("First name is required."))
        if not last_name:
            raise ValueError(_("Last name is required."))
        user = self.model(email=email, first_name=first_name, last_name=last_name, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password, **extra_fields):
        extra_fields.setdefault('first_name', 'Admin')
        extra_fields.setdefault('last_name', 'User')
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_active', True)
        extra_fields.setdefault('is_verified', True)
        extra_fields.setdefault('is_premium', True)
        return self.create_user(
            first_name=extra_fields.pop('first_name'),
            last_name=extra_fields.pop('last_name'),
            email=email,
            password=password,
            **extra_fields
        )


NIGERIAN_STATES = [
    ('Abia', 'Abia'), ('Adamawa', 'Adamawa'), ('Akwa Ibom', 'Akwa Ibom'),
    ('Anambra', 'Anambra'), ('Bauchi', 'Bauchi'), ('Bayelsa', 'Bayelsa'),
    ('Benue', 'Benue'), ('Borno', 'Borno'), ('Cross River', 'Cross River'),
    ('Delta', 'Delta'), ('Ebonyi', 'Ebonyi'), ('Edo', 'Edo'),
    ('Ekiti', 'Ekiti'), ('Enugu', 'Enugu'), ('FCT', 'FCT - Abuja'),
    ('Gombe', 'Gombe'), ('Imo', 'Imo'), ('Jigawa', 'Jigawa'),
    ('Kaduna', 'Kaduna'), ('Kano', 'Kano'), ('Katsina', 'Katsina'),
    ('Kebbi', 'Kebbi'), ('Kogi', 'Kogi'), ('Kwara', 'Kwara'),
    ('Lagos', 'Lagos'), ('Nasarawa', 'Nasarawa'), ('Niger', 'Niger'),
    ('Ogun', 'Ogun'), ('Ondo', 'Ondo'), ('Osun', 'Osun'),
    ('Oyo', 'Oyo'), ('Plateau', 'Plateau'), ('Rivers', 'Rivers'),
    ('Sokoto', 'Sokoto'), ('Taraba', 'Taraba'), ('Yobe', 'Yobe'),
    ('Zamfara', 'Zamfara'),
]


class User(AbstractBaseUser):
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    email = models.EmailField(max_length=100, unique=True)
    username = models.CharField(max_length=50, unique=True, blank=True, null=True)
    state = models.CharField(max_length=50, blank=True, null=True)
    is_superuser = models.BooleanField(default=False)
    is_staff = models.BooleanField(default=False)
    is_active = models.BooleanField(default=False)
    is_verified = models.BooleanField(default=False)
    is_premium = models.BooleanField(default=False)
    premium_expires_at = models.DateTimeField(null=True, blank=True)
    ai_insight_count = models.IntegerField(default=0)
    elite_insight_count = models.IntegerField(default=0)
    ai_limit_reset_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = UserManager()
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    def __str__(self):
        return self.email

    def has_perm(self, perm, obj=None):
        return self.is_superuser

    def has_module_perms(self, app_label):
        return self.is_superuser

    def check_premium(self):
        if self.is_superuser:
            return True
        if not self.is_premium:
            return False
        if self.premium_expires_at and timezone.now() > self.premium_expires_at:
            self.is_premium = False
            self.premium_expires_at = None
            self.save()
            return False
        return True

    def reset_daily_limits_if_needed(self):
        now = timezone.now()
        if self.ai_limit_reset_at is None or now > self.ai_limit_reset_at:
            self.ai_insight_count = 0
            self.elite_insight_count = 0
            self.ai_limit_reset_at = now + timedelta(hours=24)
            self.save()

    def get_ai_limit(self):
        return 20 if self.check_premium() else 5

    def can_use_ai_insight(self):
        if self.is_superuser:
            return True
        self.reset_daily_limits_if_needed()
        return self.ai_insight_count < self.get_ai_limit()

    def can_use_elite_insight(self):
        if self.is_superuser:
            return True
        self.reset_daily_limits_if_needed()
        return self.elite_insight_count < self.get_ai_limit()


class OTP(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='otps')
    code = models.CharField(max_length=6)
    purpose = models.CharField(max_length=20)
    is_used = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()

    def is_expired(self):
        return timezone.now() > self.expires_at

    def __str__(self):
        return f"{self.user.email} - {self.purpose} - {self.code}"