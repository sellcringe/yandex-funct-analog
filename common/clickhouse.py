from clickhouse_driver import Client
from .settings import settings

def get_clickhouse():
    client = Client(
        host=settings.CH_HOST,
        port=settings.CH_PORT,
        user=settings.CH_USER,
        password=settings.CH_PASSWORD,
        secure=settings.CH_SECURE,
        verify=settings.CH_VERIFY,
        ca_certs=settings.CH_CA_CERT or None,
        # при необходимости можно добавить settings={"readonly": 1}
    )
    return client
