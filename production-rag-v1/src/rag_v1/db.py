from contextlib import contextmanager

import psycopg
from pgvector.psycopg import register_vector

from rag_v1.config import settings


@contextmanager
def connect():
    conn = psycopg.connect(settings.database_url)
    try:
        register_vector(conn)
        yield conn
    finally:
        conn.close()
