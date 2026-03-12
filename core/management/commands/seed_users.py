from django.core.management.base import BaseCommand
from django.contrib.auth.models import User


class Command(BaseCommand):
    help = 'Create default admin and user accounts for testing'

    def handle(self, *args, **options):
        # Create Admin
        if not User.objects.filter(username='admin').exists():
            User.objects.create_superuser(
                username='admin',
                email='admin@rentalbikes.com',
                password='admin123'
            )
            self.stdout.write(self.style.SUCCESS('Admin account created: admin / admin123'))
        else:
            self.stdout.write(self.style.WARNING('Admin account already exists.'))

        # Create Regular User
        if not User.objects.filter(username='user').exists():
            User.objects.create_user(
                username='user',
                email='user@rentalbikes.com',
                password='user123'
            )
            self.stdout.write(self.style.SUCCESS('User account created: user / user123'))
        else:
            self.stdout.write(self.style.WARNING('User account already exists.'))

        self.stdout.write(self.style.SUCCESS('Done!'))
