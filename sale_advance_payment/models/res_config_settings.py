from odoo import models, fields


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    advance_account_id = fields.Many2one(
        related="company_id.advance_account_id",
        string="Advance Received Account",
        domain="[('internal_group', '=', 'liability')]",
        check_company=True,
        readonly=False,
        help="Account to record customer advance payment."
    )
