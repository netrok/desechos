from django.db import migrations

SQL = """
-- Secuencia concurrente para el consecutivo SIS
CREATE SEQUENCE IF NOT EXISTS inventario_item_codigo_seq START 1;

-- Función trigger: si codigo viene vacío/null, asigna SIS + consecutivo con padding
CREATE OR REPLACE FUNCTION inventario_set_codigo_sis()
RETURNS trigger AS $$
BEGIN
  IF NEW.codigo IS NULL OR btrim(NEW.codigo) = '' THEN
    NEW.codigo := 'SIS' || lpad(nextval('inventario_item_codigo_seq')::text, 3, '0');
  END IF;

  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger BEFORE INSERT (idempotente)
DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_trigger WHERE tgname = 'tr_inventario_item_set_codigo_sis'
  ) THEN
    CREATE TRIGGER tr_inventario_item_set_codigo_sis
    BEFORE INSERT ON inventario_inventarioitem
    FOR EACH ROW
    EXECUTE FUNCTION inventario_set_codigo_sis();
  END IF;
END $$;
"""

REVERSE_SQL = """
DROP TRIGGER IF EXISTS tr_inventario_item_set_codigo_sis ON inventario_inventarioitem;
DROP FUNCTION IF EXISTS inventario_set_codigo_sis();
DROP SEQUENCE IF EXISTS inventario_item_codigo_seq;
"""


class Migration(migrations.Migration):

    dependencies = [
        ("inventario", "0001_initial"),
    ]

    operations = [
        migrations.RunSQL(SQL, reverse_sql=REVERSE_SQL),
    ]
