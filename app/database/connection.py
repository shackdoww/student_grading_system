import os
from contextlib import contextmanager
from contextvars import ContextVar

import psycopg
from dotenv import load_dotenv

load_dotenv()
_actor = ContextVar('grade_audit_actor', default='system')


@contextmanager
def audit_actor(username):
    token = _actor.set(username)
    try:
        yield
    finally:
        _actor.reset(token)


def get_connection():
    connection = psycopg.connect(
        host=os.getenv("DB_HOST"),
        port=os.getenv("DB_PORT"),
        dbname=os.getenv("DB_NAME"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        connect_timeout=5
    )
    connection.execute("SELECT set_config('app.actor', %s, false)", (_actor.get(),))
    connection.commit()
    return connection
