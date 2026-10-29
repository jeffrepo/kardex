from odoo import fields, models


class ResCompany(models.Model):
    _inherit = 'res.company'

    kardex_tz = fields.Selection(
        related='partner_id.tz', readonly=False,
        string='Zona horaria del Kardex',
        help='Zona horaria de la compañía para las fechas de los reportes Kardex. '
             'Si está vacía, se utiliza la zona horaria del usuario.')
