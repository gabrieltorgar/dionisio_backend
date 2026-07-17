"""Factories del modelo de usuario."""

import factory
from django.contrib.auth import get_user_model

User = get_user_model()


class UserFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = User
        django_get_or_create = ("email",)

    email = factory.Sequence(lambda n: f"user{n}@dionisio.app")
    first_name = factory.Sequence(lambda n: f"Nombre {n}")
    last_name = "Apellido"
    is_active = True

    @factory.post_generation
    def password(self, create, extracted, **kwargs):
        if not create:
            return
        self.set_password(extracted or "pass1234")
        self.save()
