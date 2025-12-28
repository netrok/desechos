from django.db import migrations

FORWARD_SQL = """
CREATE SEQUENCE IF NOT EXISTS ventas_folio_seq;

CREATE OR REPLACE FUNCTION ventas_set_folio()
RETURNS trigger AS $$
BEGIN
  IF NEW.folio IS NULL OR NEW.folio = '' THEN
    NEW.folio :=
      'VTA-' || to_char(CURRENT_DATE, 'YYYYMMDD') || '-' ||
      lpad(nextval('ventas_folio_seq'::regclass)::text, 8, '0');
  END IF;

  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_ventas_set_folio ON ventas_venta;

CREATE TRIGGER trg_ventas_set_folio
BEFORE INSERT ON ventas_venta
FOR EACH ROW
EXECUTE FUNCTION ventas_set_folio();
"""

REVERSE_SQL = """
DROP TRIGGER IF EXISTS trg_ventas_set_folio ON ventas_venta;
DROP FUNCTION IF EXISTS ventas_set_folio();
DROP SEQUENCE IF EXISTS ventas_folio_seq;
"""


class Migration(migrations.Migration):
    dependencies = [
        ("ventas", "0001_initial"),  # <-- cámbialo por tu ÚLTIMA migración real de ventas
    ]

    operations = [
        migrations.RunSQL(FORWARD_SQL, REVERSE_SQL),
    ]
