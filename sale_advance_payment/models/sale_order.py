# -*- coding: utf-8 -*-
from odoo import fields, models, _
from odoo.exceptions import UserError


class SaleOrder(models.Model):
    _inherit = "sale.order"

    advance_payment = fields.Monetary(
        string="Advance Payment",
        currency_field="currency_id",
        help="Advance amount from customer"
    )

    advance_entry_id = fields.Many2one(
        "account.move",
        string="Adv. Journal Entry",
        readonly=True,
        copy=False,
        help="journal entry created for advance payment."
    )

    def _create_advance_payment_entry(self):
        self.ensure_one()
        if self.advance_entry_id:
            return True
        partner = self.partner_id
        amount = self.advance_payment
        company = self.company_id

        receivable_account = partner.property_account_receivable_id
        if not receivable_account:
            raise UserError(
                _("No receivable account is set for customer %s.") % self.partner_id.name)

        advance_account = company.advance_account_id
        if not advance_account:
            raise UserError(
                _("Please configure an Advance Received account in accounting settings."))

        journal = self.env.ref('sale_advance_payment.journal_advance_payment')
        if not journal:
            raise UserError(
                _("No journal found for advance payment entries."))

        move_lines = [
            (0, 0, {
                'name': f"Advance Payment - {self.name}",
                'partner_id': partner.id,
                'account_id': receivable_account.id,
                'debit': amount,
                'credit': 0.0,
            }),
            (0, 0, {
                'name': f"Advance Payment - {self.name}",
                'partner_id': partner.id,
                'account_id': advance_account.id,
                'credit': amount,
                'debit': 0.0,
            }),
        ]
        move_vals = {
            'ref': f"Advance for {self.name}",
            'move_type': 'entry',
            'date': fields.Date.context_today(self),
            'journal_id': journal.id,
            'company_id': company.id,
            'partner_id': partner.id,
            'line_ids': move_lines,
        }

        move = self.env['account.move'].create(move_vals)
        move.action_post()

        self.advance_entry_id = move.id

        body = _(
            "Journal Entry: %s", self._get_html_link(title=move.name)
        )
        self.message_post(body=body)

        return move

    def action_confirm(self):
        res = super().action_confirm()
        for order in self:
            if order.advance_payment > 0:
                order._create_advance_payment_entry()
        return res

    def action_view_advance_entry(self):
        self.ensure_one()
        if not self.advance_entry_id:
            raise UserError(
                _("No advance journal entry has been created yet."))

        return {
            'type': 'ir.actions.act_window',
            'name': _('Advance Payment'),
            'res_model': 'account.move',
            'view_mode': 'form',
            'res_id': self.advance_entry_id.id,
            'target': 'current',
            'context': {'create': False},
        }
