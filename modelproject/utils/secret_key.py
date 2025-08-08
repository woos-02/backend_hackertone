from django.core.management.utils import get_random_secret_key


def get_new_secret_key_for_dev() -> str:
    return "develop-" + get_random_secret_key()


def get_new_secret_key_for_prod() -> str:
    return get_random_secret_key()