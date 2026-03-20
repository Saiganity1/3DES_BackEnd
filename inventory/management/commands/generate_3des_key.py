import base64

from Crypto.Random import get_random_bytes
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Generate a random 24-byte Triple DES key (base64) for INVENTORY_3DES_KEY_B64."

    def handle(self, *args, **options):
        key = get_random_bytes(24)
        self.stdout.write(base64.b64encode(key).decode("ascii"))
