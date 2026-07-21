from django.contrib.auth.models import Group, User
from django.core.management.base import BaseCommand

EXPENSE_ONLY_GROUP = "Expense Only"


class Command(BaseCommand):
    help = (
        "Creates (or updates) a login restricted to the Expense Management pages "
        "only, via the 'Expense Only' group. Default username/password: expense/exp123."
    )

    def add_arguments(self, parser):
        parser.add_argument("username", nargs="?", default="expense")
        parser.add_argument("password", nargs="?", default="exp123")

    def handle(self, *args, **options):
        username = options["username"]
        password = options["password"]

        group, _ = Group.objects.get_or_create(name=EXPENSE_ONLY_GROUP)

        user, created = User.objects.get_or_create(username=username)
        user.is_staff = False
        user.is_superuser = False
        user.set_password(password)
        user.save()
        user.groups.set([group])

        action = "Created" if created else "Updated"
        self.stdout.write(self.style.SUCCESS(
            f"{action} user '{username}' - restricted to Expense Management only."
        ))
