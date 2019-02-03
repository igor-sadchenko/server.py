""" Sqlalchemy session and engine for DB.
"""
from contextlib import contextmanager
from functools import wraps

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from config import CONFIG

engine = create_engine(
    'postgresql://{user}:{password}@{hostname}:{port}/{db_name}'.format(
        user=CONFIG.DB_USER,
        password=CONFIG.DB_PASSWORD,
        hostname=CONFIG.DB_HOST,
        port=CONFIG.DB_PORT,
        db_name=CONFIG.DB_NAME
    )
)
Session = sessionmaker(bind=engine)


@contextmanager
def session_ctx():
    session = Session(expire_on_commit=False)
    try:
        yield session
        session.commit()
    except:
        session.rollback()
        raise
    finally:
        session.close()


def session_wrapper(function):
    @wraps(function)
    def wrapped(*args, **kwargs):
        if kwargs.get('session', None) is None:
            with session_ctx() as session:
                kwargs['session'] = session
                return function(*args, **kwargs)
        else:
            return function(*args, **kwargs)
    return wrapped
