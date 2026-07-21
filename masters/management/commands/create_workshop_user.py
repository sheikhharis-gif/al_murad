from django.contrib.auth.models import Group, User
from django.core.management.base import BaseCommand

WORKSHOP_ONLY_GROUP = "Workshop Only"


class Command(BaseCommand):
    help = (
        "Creates (or updates) a login restricted to the Maintenance/Workshop pages "
        "only, via the 'Workshop Only' group. Default username/password: workshop/workshop123."
    )

    def add_arguments(self, parser):
        parser.add_argument("username", nargs="?", default="workshop")
        parser.add_argument("password", nargs="?", default="workshop123")

    def handle(self, *args, **options):
        username = options["username"]
        password = options["password"]

        group, _ = Group.objects.get_or_create(name=WORKSHOP_ONLY_GROUP)

        user, created = User.objects.get_or_create(username=username)
        user.is_staff = False
        user.is_superuser = False
        user.set_password(password)
        user.save()
        user.groups.set([group])

        action = "Created" if created else "Updated"
        self.stdout.write(self.style.SUCCESS(
            f"{action} user '{username}' - restricted to Workshop/Maintenance only."
        ))
