"""Manager del modelo de usuario, autenticado por correo electrónico."""

from django.contrib.auth.models import BaseUserManager


class UserManager(BaseUserManager):
    """Manager de `User` que usa el correo como identificador único."""

    use_in_migrations = True

    def _create_user(self, email, password, **extra_fields):
        """Crea y guarda un usuario con el correo y la contraseña dados."""
        if not email:
            raise ValueError("El correo electrónico es obligatorio")
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, email=None, password=None, **extra_fields):
        """Crea un usuario estándar (sin privilegios de staff/superusuario)."""
        extra_fields.setdefault("is_staff", False)
        extra_fields.setdefault("is_superuser", False)
        return self._create_user(email, password, **extra_fields)

    def create_superuser(self, email, password=None, **extra_fields):
        """Crea un superusuario con acceso al admin de Django."""
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)

        if extra_fields.get("is_staff") is not True:
            raise ValueError("El superusuario debe tener is_staff=True.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("El superusuario debe tener is_superuser=True.")

        return self._create_user(email, password, **extra_fields)
