from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError


class SaleDiscountRule(models.Model):
    _name = "sale.discount.rule"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _description = "Sales Discount Rule"

    name = fields.Char("Rule Name", required=True, tracking=True)
    min_amount = fields.Float("Minimum Amount", required=True, tracking=True)
    max_amount = fields.Float("Maximum Amount", required=True, tracking=True)
    discount_percent = fields.Float(
        "Discount (%)", required=True, tracking=True)
    customer_group_id = fields.Many2one(
        "res.partner.category", string="Customer Group", required=False, tracking=True
    )
    valid_from = fields.Date("Valid From", required=True, tracking=True)
    valid_to = fields.Date("Valid To", required=True, tracking=True)

    @api.constrains("min_amount", "max_amount")
    def _check_amount_range(self):
        for rec in self:
            if rec.max_amount < rec.min_amount:
                raise ValidationError(
                    _("Maximum amount must be greater than or equal to minimum amount."))
            if rec.max_amount <= 0:
                raise ValidationError(
                    _("Maximum amount must be greater than 0.")
                )

    @api.constrains("valid_from", "valid_to")
    def _check_validity_dates(self):
        for rec in self:
            if rec.valid_from and rec.valid_to and rec.valid_from > rec.valid_to:
                raise ValidationError(
                    _("Valid To must be greater than or equal to Valid From."))

    @api.constrains("discount_percent")
    def _check_discount_percent(self):
        for rec in self:
            if rec.discount_percent <= 0 or rec.discount_percent > 1:
                raise ValidationError(
                    _("Discount must be greater than 0 and less than or equal to 100."))

    def unlink(self):
        used_orders = self.env["sale.order"].search(
            [("applied_discount_rule_id", "in", self.ids)], limit=1)
        if used_orders:
            raise UserError(
                _("You cannot delete a discount rule that is used in a Sale Order."))
        return super().unlink()
