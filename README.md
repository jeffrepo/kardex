# kardex
Modulo de Odoo para imprimir un kardex

## Zona horaria (Odoo 13.0)

Los reportes PDF y Excel muestran la columna **Fecha** y el rango de fechas
en la zona horaria del contacto de la compañía de la ubicación seleccionada
(`res.company.partner_id.tz`). Si la ubicación es compartida, se utiliza la
compañía activa. Si el contacto de la compañía no tiene zona horaria, se usa
la del contexto/usuario y, finalmente, UTC.

Configure **Ajustes → Usuarios y compañías → Compañías → Zona horaria del Kardex**,
por ejemplo
`America/Mexico_City`, `America/Cancun` o `America/Guatemala`, según corresponda.
La zona debe elegirse por ciudad/región: un país puede tener varias zonas.
El campo edita la zona horaria del contacto de la compañía, sin duplicarla.
La conversión utiliza las reglas de `pytz` instaladas en el servidor; mantenga
esa dependencia actualizada para aplicar los cambios de horario de cada país.

Las fechas de los movimientos y los filtros se conservan en UTC; la conversión
se realiza solamente al presentar el reporte, incluyendo cambios de día.
Los campos del asistente siguen la zona horaria del usuario, como los demás
campos de fecha y hora de Odoo.

Después de instalar este cambio, reinicie Odoo y actualice el módulo `kardex`
para cargar la plantilla PDF actualizada.

Pruebas de integración en una base de pruebas de Odoo 13.0:

```sh
odoo-bin -d kardex_test -i kardex --test-enable --test-tags /kardex --stop-after-init
```
