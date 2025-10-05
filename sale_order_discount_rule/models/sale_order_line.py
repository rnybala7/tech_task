# -*- coding: utf-8 -*-
from odoo import models


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    def write(self, vals):
        res = super().write(vals)
        tracked_fields = {"product_id", "product_uom_qty", "price_unit"}
        if any(f in vals for f in tracked_fields):
            self.order_id._apply_best_discount()
        return res
