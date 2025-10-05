from odoo import models, fields


class ResCompany(models.Model):
    _inherit = "res.company"

    advance_account_id = fields.Many2one(
        "account.account",
        string="Advance Received Account",
        domain="[('internal_group', '=', 'liability')]",
        check_company=True,
        help="Account to record customer advance payment."
    )
