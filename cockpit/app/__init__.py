"""Cockpit application package with lazy entrypoint import."""


def run_cockpit(*args, **kwargs):
    """Start the cockpit without eagerly importing MainWindow during package import."""
    from .main import run_cockpit as _run_cockpit
    return _run_cockpit(*args, **kwargs)


__all__ = ["run_cockpit"]
