import threading

_thread_locals = threading.local()


def set_current_user(user):
    """Définit l'utilisateur courant dans le contexte du thread."""
    _thread_locals.user = user


def get_current_user():
    """Récupère l'utilisateur courant depuis le contexte du thread."""
    return getattr(_thread_locals, 'user', None)
