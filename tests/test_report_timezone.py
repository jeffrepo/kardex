import base64
import io
from datetime import datetime
from xml.etree import ElementTree
from zipfile import ZipFile

from odoo.tests.common import SavepointCase


class TestReportTimezone(SavepointCase):
    @classmethod
    def setUpClass(cls):
        super(TestReportTimezone, cls).setUpClass()
        cls.env.company.partner_id.tz = 'America/Mexico_City'
        cls.report = cls.env['report.kardex.reporte_kardex'].with_context(tz='Asia/Tokyo')
        cls.location = cls.env['stock.location'].create({
            'name': 'Kardex timezone test',
            'usage': 'internal',
            'company_id': cls.env.company.id,
        })
        cls.product = cls.env['product.product'].create({'name': 'Kardex timezone test'})
        cls.utc_date = datetime(2026, 1, 15, 2, 30)
        # Completed movement fixture: reporting must preserve its UTC timestamp.
        supplier = cls.env.ref('stock.stock_location_suppliers')
        move = cls.env['stock.move'].create({
            'name': 'Kardex timezone test',
            'product_id': cls.product.id,
            'product_uom': cls.product.uom_id.id,
            'product_uom_qty': 1,
            'location_id': supplier.id,
            'location_dest_id': cls.location.id,
            'company_id': cls.env.company.id,
            'state': 'done',
        })
        cls.move_line = cls.env['stock.move.line'].create({
            'move_id': move.id,
            'product_id': cls.product.id,
            'product_uom_id': cls.product.uom_id.id,
            'qty_done': 1,
            'location_id': supplier.id,
            'location_dest_id': cls.location.id,
            'company_id': cls.env.company.id,
            'date': cls.utc_date,
        })
        cls.wizard = cls.env['kardex.asistente_kardex'].with_context(tz='Asia/Tokyo').create({
            'ubicacion_id': cls.location.id,
            'producto_ids': [(6, 0, cls.product.ids)],
            'fecha_desde': datetime(2026, 1, 15, 0, 0),
            'fecha_hasta': datetime(2026, 1, 15, 6, 0),
        })

    def test_company_timezone_takes_priority_over_user_context(self):
        self.assertEqual(self.report._get_report_timezone(self.location), 'America/Mexico_City')

    def test_company_timezone_setting_updates_the_company_contact(self):
        self.env.company.kardex_tz = 'America/Cancun'
        self.assertEqual(self.env.company.partner_id.tz, 'America/Cancun')
        self.assertEqual(self.report._get_report_timezone(self.location), 'America/Cancun')

    def test_location_company_takes_priority_over_active_company(self):
        partner = self.env['res.partner'].new({'tz': 'America/Guatemala'})
        company = self.env['res.company'].new({'partner_id': partner.id})
        location = self.env['stock.location'].new({'company_id': company.id})
        self.assertEqual(self.report._get_report_timezone(location), 'America/Guatemala')

    def test_shared_location_uses_active_company(self):
        location = self.env['stock.location'].new({'company_id': False})
        self.assertEqual(self.report._get_report_timezone(location), 'America/Mexico_City')

    def test_missing_company_timezone_falls_back_to_context_user_then_utc(self):
        self.env.company.partner_id.tz = False
        self.env.user.tz = 'America/Guatemala'
        self.assertEqual(self.report._get_report_timezone(self.location), 'Asia/Tokyo')
        report = self.report.with_context(tz=False)
        self.assertEqual(report._get_report_timezone(self.location), 'America/Guatemala')
        self.env.user.tz = False
        self.assertEqual(report._get_report_timezone(self.location), 'UTC')

    def test_local_dates_and_historical_dst(self):
        cases = [
            ('2026-01-15 02:30:00', 'America/Mexico_City', '14/01/2026 20:30:00'),
            ('2026-07-15 02:30:00', 'America/Mexico_City', '14/07/2026 20:30:00'),
            ('2020-07-15 02:30:00', 'America/Mexico_City', '14/07/2020 21:30:00'),
            ('2026-01-15 02:30:00', 'America/Cancun', '14/01/2026 21:30:00'),
            ('2026-01-15 02:30:00', 'America/Guatemala', '14/01/2026 20:30:00'),
            ('2026-01-15 02:30:00', 'Asia/Kolkata', '15/01/2026 08:00:00'),
            ('2026-01-15 02:30:00', 'UTC', '15/01/2026 02:30:00'),
        ]
        for value, tz, expected in cases:
            with self.subTest(value=value, tz=tz):
                self.assertEqual(self.report._format_datetime(value, tz), expected)
        self.assertEqual(
            self.report._format_datetime(self.utc_date, 'America/Mexico_City'),
            '14/01/2026 20:30:00')
        self.assertEqual(self.report._format_datetime(False, 'UTC'), '')

    def test_report_lines_and_filters_stay_in_utc(self):
        data = self.wizard.read()[0]
        result = self.report.lineas(data, self.product.id)
        self.assertEqual(len(result['lineas']), 1)
        self.assertEqual(result['lineas'][0]['fecha'], self.utc_date)
        self.assertEqual(result['totales']['entrada'], 1)
        data['fecha_desde'] = datetime(2026, 1, 15, 3, 0)
        self.assertFalse(self.report.lineas(data, self.product.id)['lineas'])
        self.assertEqual(self.move_line.date, self.utc_date)

    def test_excel_uses_company_timezone_for_headers_and_movements(self):
        self.wizard.reporte_excel()
        ns = {'s': 'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}
        with ZipFile(io.BytesIO(base64.b64decode(self.wizard.archivo_excel))) as workbook:
            strings = ElementTree.fromstring(workbook.read('xl/sharedStrings.xml'))
            strings = [''.join(item.itertext()) for item in strings]
            sheet = ElementTree.fromstring(workbook.read('xl/worksheets/sheet1.xml'))
            cells = {
                cell.attrib['r']: strings[int(cell.find('s:v', ns).text)]
                for cell in sheet.findall('.//s:c', ns)
                if cell.attrib.get('t') == 's'
            }
        self.assertEqual(cells['A4'], '14/01/2026 18:00:00')
        self.assertEqual(cells['B4'], '15/01/2026 00:00:00')
        self.assertEqual(cells['A9'], '14/01/2026 20:30:00')
        self.assertEqual(self.move_line.date, self.utc_date)

    def test_pdf_template_uses_company_timezone_without_double_conversion(self):
        action = self.env.ref('kardex.action_reporte_kardex').with_context(
            active_model=self.wizard._name, active_ids=self.wizard.ids, tz='Asia/Tokyo')
        html, _ = action.render_qweb_html(self.wizard.ids, data={'form': self.wizard.read()[0]})
        self.assertIn(b'14/01/2026 18:00:00', html)
        self.assertIn(b'15/01/2026 00:00:00', html)
        self.assertIn(b'14/01/2026 20:30:00', html)
        self.assertNotIn(b'15/01/2026 11:30:00', html)
