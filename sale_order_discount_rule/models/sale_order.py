# -*- coding: utf-8 -*-
from odoo import api, fields, models
from datetime import date


class SaleOrder(models.Model):
    _inherit = "sale.order"

    applied_discount_rule_id = fields.Many2one(
        "sale.discount.rule", string="Discount Rule", readonly=True, ondelete="restrict",
    )
    discount_percent = fields.Float("Discount (%)", readonly=True)

    @api.model_create_multi
    def create(self, vals_list):
        orders = super().create(vals_list)
        orders._apply_best_discount()
        return orders

    def _apply_best_discount(self):
        today = date.today()
        for order in self:
            amount_total = sum(
                line.product_uom_qty * line.price_unit for line in order.order_line if not line.display_type)
            customer_groups = order.partner_id.category_id.ids

            domain = [
                ("min_amount", "<=", amount_total),
                ("max_amount", ">=", amount_total),
                ("valid_from", "<=", today),
                ("valid_to", ">=", today)]

            if customer_groups:
                domain.append(("customer_group_id", "in", customer_groups))
            else:
                domain.append(("customer_group_id", "=", False))

            rule = self.env["sale.discount.rule"].search(
                domain, order="discount_percent desc", limit=1)

            if rule:
                order.applied_discount_rule_id = rule.id
                applied_percent = (rule.discount_percent * 100)
                order.discount_percent = applied_percent
                order._apply_discount_to_lines(applied_percent)
            else:
                order.applied_discount_rule_id = False
                order.discount_percent = 0.0
                order._apply_discount_to_lines(0.0)

    def _apply_discount_to_lines(self, discount_percent):
        for order in self:
            lines_to_update = order.order_line.filtered(
                lambda l: not l.display_type)
            if lines_to_update:
                lines_to_update.write({'discount': discount_percent})
        return True

    def action_reapply_discount(self):
        self._apply_best_discount()
