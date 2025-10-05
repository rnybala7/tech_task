from odoo import models, fields, api, _
import base64
import io
import xlsxwriter
from collections import defaultdict
from odoo.exceptions import ValidationError


class SaleProfitabilityWizard(models.TransientModel):
    _name = "sale.profitability.wizard"
    _description = "Sales Profitability Report Wizard"

    start_date = fields.Date(string="Start Date", required=True)
    end_date = fields.Date(string="End Date", required=True)
    customer_ids = fields.Many2many(
        "res.partner", string="Customers")
    category_ids = fields.Many2many(
        "product.category", string="Product Categories")
    excel_file = fields.Binary('File', readonly=True)
    file_name = fields.Char('Filename', readonly=True)

    @api.constrains('start_date', 'end_date')
    def _check_date_range(self):
        for rec in self:
            if rec.end_date < rec.start_date:
                raise ValidationError(
                    _("End Date must be greater than or equal to Start Date."))

    def action_view_report(self):
        data = {
            'start_date': self.start_date.strftime('%m-%d-%Y'),
            'end_date': self.end_date.strftime('%m-%d-%Y'),
            'customer_ids': self.customer_ids.mapped('name'),
            'category_ids': self.category_ids.mapped('name'),
            'lines': self._get_profitability_data(),
        }
        return self.env.ref('sale_profitability_report.action_report_sale_profitability').report_action(None, data=data)

    def _get_profitability_data(self):
        line_domain = [
            ('order_id.date_order', '>=', self.start_date),
            ('order_id.date_order', '<=', self.end_date),
            ('order_id.state', 'in', ['sale', 'done']),
            ('display_type', '=', False),
        ]

        if self.customer_ids:
            line_domain.append(
                ('order_id.partner_id', 'in', self.customer_ids.ids))

        if self.category_ids:
            line_domain.append(
                ('product_id.categ_id', 'in', self.category_ids.ids))

        all_lines = self.env['sale.order.line'].search(line_domain)
        if not all_lines:
            return []

        all_lines.mapped('product_id.categ_id')
        all_lines.mapped('order_id.partner_id')

        order_data = defaultdict(lambda: {
            'revenue': 0.0,
            'cost': 0.0,
            'margin': 0.0,
            'categories': set()
        })

        for line in all_lines:
            order_bucket = order_data[line.order_id.id]
            product = line.product_id
            revenue = line.price_total
            cost = product.standard_price * line.product_uom_qty

            order_bucket['revenue'] += revenue
            order_bucket['cost'] += cost

            if product.categ_id:
                order_bucket['categories'].add(product.categ_id.name)

        results = []
        orders = self.env['sale.order'].browse(list(order_data.keys()))

        sno = 1
        total_revenue = total_cost = total_margin = 0.0
        for order in orders:
            data = order_data[order.id]
            if data['revenue'] == 0.0 and data['cost'] == 0.0:
                continue
            revenue = data['revenue']
            cost = data['cost']
            margin = revenue - cost

            total_revenue += revenue
            total_cost += cost
            total_margin += margin

            results.append({
                'sno': sno,
                'order': order.name,
                'customer': order.partner_id.name,
                'date': order.date_order.strftime('%m-%d-%Y'),
                'category': ', '.join(sorted(data['categories'])) or 'Uncategorized',
                'revenue': revenue,
                'cost': data['cost'],
                'margin': margin,
            })
            sno += 1
        results.append({
            'sno': '',
            'order': 'TOTAL',
            'customer': '',
            'date': '',
            'category': '',
            'revenue': total_revenue,
            'cost': total_cost,
            'margin': total_margin,
        })
        return results

    def action_export_excel(self):
        self.ensure_one()
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        sheet = workbook.add_worksheet("Sales Profitability")

        sheet.set_column(0, 0, 10)
        sheet.set_column(1, 1, 15)
        sheet.set_column(2, 2, 25)
        sheet.set_column(3, 3, 15)
        sheet.set_column(4, 4, 20)
        sheet.set_column(5, 5, 15)
        sheet.set_column(6, 6, 15)
        sheet.set_column(7, 7, 15)

        title_format = workbook.add_format(
            {'bold': True, 'font_size': 16, 'align': 'center'})
        header_format = workbook.add_format(
            {'bold': True, 'bg_color': '#D9E1F2', 'font_size': 12, 'align': 'center'})
        money_format = workbook.add_format({'num_format': '#,##0.00'})
        total_format = workbook.add_format(
            {'bold': True, 'bg_color': '#D9E1F2'})
        total_money_format = workbook.add_format(
            {'bold': True, 'bg_color': '#D9E1F2', 'num_format': '#,##0.00'})
        bold_format = workbook.add_format({'bold': True})
        date_format = workbook.add_format(
            {'num_format': 'MM/dd/yyyy', 'align': 'left', 'bold': True})
        text_format = workbook.add_format({'align': 'center'})

        customer_names = ', '.join(self.customer_ids.mapped(
            'name')) if self.customer_ids else 'All Customers'
        category_names = ', '.join(self.category_ids.mapped(
            'name')) if self.category_ids else 'All Categories'

        row = 0
        sheet.merge_range(
            row, 0, row, 7, "Sales Profitability Report", title_format)
        row += 2

        sheet.write(row, 0, "From Date", bold_format)
        sheet.write(row, 1, self.start_date, date_format)
        sheet.write(row, 2, "To Date", bold_format)
        sheet.write(
            row, 3, self.end_date, date_format)
        row += 1

        sheet.write(row, 0, "Customers", bold_format)
        sheet.write(row, 1, customer_names, bold_format)
        row += 1

        sheet.write(row, 0, "Categories", bold_format)
        sheet.write(row, 1, category_names, bold_format)
        row += 2

        headers = ["Sno", "Order", "Customer", "Date", "Category",
                   "Revenue", "Cost", "Margin"]
        for col, header in enumerate(headers):
            sheet.write(row, col, header, header_format)

        row += 1
        data = self._get_profitability_data()
        for rec in data:
            if rec['order'] == 'TOTAL':
                sheet.write(row, 0, '')
                sheet.write(row, 1, '')
                sheet.write(row, 2, '')
                sheet.write(row, 3, '')
                sheet.write(row, 4, 'TOTAL', total_format)
                sheet.write(row, 5, rec['revenue'], total_money_format)
                sheet.write(row, 6, rec['cost'], total_money_format)
                sheet.write(row, 7, rec['margin'], total_money_format)
            else:
                sheet.write(row, 0, rec['sno'], text_format)
                sheet.write(row, 1, rec['order'])
                sheet.write(row, 2, rec['customer'])
                sheet.write(row, 3, rec['date'])
                sheet.write(row, 4, rec['category'])
                sheet.write(row, 5, rec['revenue'], money_format)
                sheet.write(row, 6, rec['cost'], money_format)
                sheet.write(row, 7, rec['margin'], money_format)
            row += 1

        workbook.close()
        output.seek(0)
        file_data = base64.b64encode(output.read())
        output.close()
        filename = f"Sales_Profitability.xlsx"
        self.write({'excel_file': file_data, 'file_name': filename})

        return {
            'type': 'ir.actions.act_url',
            'url': '/web/content/?model=%s&id=%s&field=%s&filename=Sales_Profitability.xlsx&download=true' % (self._name, self.id, 'excel_file'),
            'target': 'new',
        }
