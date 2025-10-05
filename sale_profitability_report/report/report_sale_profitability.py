from odoo import models, api


class SaleProfitabilityReport(models.AbstractModel):
    _name = 'report.sale_profitability_report.report_sale_profit_template'
    _description = 'Sales Profitability Report'

    @api.model
    def _get_report_values(self, docids, data=None):
        if not data:
            data = {}
        return {
            'data': data,
        }
