from django.db import connection

SEQ_NAME = "inventario_item_codigo_seq"

def next_codigo_num() -> int:
    with connection.cursor() as cursor:
        cursor.execute(f"SELECT nextval('{SEQ_NAME}')")
        (val,) = cursor.fetchone()
        return int(val)

def format_codigo(n: int) -> str:
    # SIS001, SIS002... cuando crezca será SIS1000 etc.
    return f"SIS{str(n).zfill(3)}"
