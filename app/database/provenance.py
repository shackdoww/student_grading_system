"""Source references are distinct from the trusted signed-in audit actor."""
from contextlib import contextmanager
from contextvars import ContextVar

_source = ContextVar('record_source_reference', default='')


def source_reference():
    return _source.get()


@contextmanager
def write_source(reference=None):
    reference = str(reference or '').strip()
    if len(reference) > 500 or any(ord(c) < 32 for c in reference):
        raise ValueError('Source reference must be a single line of at most 500 characters.')
    token = _source.set(reference)
    try:
        yield
    finally:
        _source.reset(token)
