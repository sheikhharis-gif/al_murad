from django.contrib.auth.models import User
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = (
        "Renames the existing 'admin' superuser to the given username (default "
        "'kashif') and sets its password (default 'kashif12345'). If no 'admin' "
        "user exists, creates/updates a superuser with that username instead."
    )

    def add_arguments(self, parser):
        parser.add_argument("username", nargs="?", default="kashif")
        parser.add_argument("password", nargs="?", default="kashif12345")

    def handle(self, *args, **options):
        username = options["username"]
        password = options["password"]

        old_admin = User.objects.filter(username="admin").exclude(username=username).first()
        if old_admin:
            old_admin.username = username
            old_admin.is_staff = True
            old_admin.is_superuser = True
            old_admin.set_password(password)
            old_admin.save()
            self.stdout.write(self.style.SUCCESS(
                f"Renamed 'admin' -> '{username}' and updated its password."
            ))
            return

        user, created = User.objects.get_or_create(username=username)
        user.is_staff = True
        user.is_superuser = True
        user.set_password(password)
        user.save()
        action = "Created" if created else "Updated"
        self.stdout.write(self.style.SUCCESS(f"{action} superuser '{username}'."))
