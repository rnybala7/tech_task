# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import UserError
import logging

_logger = logging.getLogger(__name__)


class PurchaseOrder(models.Model):
    _inherit = "purchase.order"

    state = fields.Selection(selection_add=[
        ('to_approve', 'To Approve'),
        ('approved_level1', 'Approved (Level 1)'),
        ('approved_level2', 'Approved (Level 2)'),
        ('rejected', 'Rejected'),
    ], ondelete={'to_approve': 'set default',
                 'approved_level1': 'set default',
                 'approved_level2': 'set default',
                 'rejected': 'set default'
                 })
    approval_required_level = fields.Selection([
        ('auto', 'Auto-Approved'),
        ('level1', 'Level 1'),
        ('level2', 'Level 2'),
    ], string='Required Approval Level', compute='_compute_approval_level', store=True, copy=False)
    # approval info fields
    level1_approved_user_id = fields.Many2one(
        'res.users', string="L1 Approved User")
    level1_approved_date = fields.Datetime(string="L1 Approved Date")
    level2_approved_user_id = fields.Many2one(
        'res.users', string="L2 Approved User")
    level2_approved_date = fields.Datetime(string="L2 Approved Date")
    rejected_uid = fields.Many2one(
        'res.users', string="Rejected By")

    @api.depends('amount_total')
    def _compute_approval_level(self):
        for order in self:
            amount = order.amount_total
            if amount <= 5000:
                order.approval_required_level = 'auto'
            elif 5000 < amount <= 20000:
                order.approval_required_level = 'level1'
            else:
                order.approval_required_level = 'level2'

    def _send_approval_notification(self, level):
        self.ensure_one()
        local_context = self.env.context.copy()
        local_context['level'] = level.replace('level', 'Level ')
        template = self.env.ref(
            "po_three_level_approval.email_template_approve_purchase_order", raise_if_not_found=False)
        level_groups = {
            'level1': 'po_three_level_approval.group_po_approve_level1',
            'level2': 'po_three_level_approval.group_po_approve_level2',
        }
        group_xmlid = level_groups.get(level)
        if not group_xmlid:
            _logger.warning("Invalid approval level: %s", level)
            return
        group = self.env.ref(group_xmlid, raise_if_not_found=False)
        if not group or not group.users:
            _logger.warning("No users found for group: %s", group_xmlid)
            return
        email_list = [user.email for user in group.users if user.email]
        if not email_list:
            _logger.warning(
                "No email addresses found for group: %s", group.name)
            return
        try:
            body = _(
                "Purchase Order %s is submitted for %s approval.",
                self._get_html_link(title=self.name),
                level.replace('level', 'Level '),
            )
            self.message_post(body=body)

            template.with_context(local_context).send_mail(
                self.id,
                force_send=True,
                email_values={'email_to': ','.join(email_list)}
            )
            _logger.info(
                "Approval notification for PO %s sent to group %s (%s)",
                self.name, group.name, ', '.join(email_list)
            )
        except Exception as e:
            _logger.error(
                "Failed to send approval notification for PO %s: %s", self.name, e)

    def button_confirm(self):
        """Override confirm func for 3 level approval"""
        for order in self:
            order._compute_approval_level()
            if order.approval_required_level == 'auto':
                return super(PurchaseOrder, order).button_confirm()
            elif order.approval_required_level == 'level1' or order.approval_required_level == 'level2':
                order.state = 'to_approve'
                order._send_approval_notification('level1')
        return True

    def action_approve_level1(self):
        if not self.env.user.has_group('po_three_level_approval.group_po_approve_level1'):
            raise UserError(
                _("You don't have access to Level 1 approval."))
        now = fields.Datetime.now()
        for rec in self:
            rec.level1_approved_user_id = self.env.uid
            rec.level1_approved_date = now
            if rec.approval_required_level == 'level1':
                rec.button_approve()
                body = _(
                    "Purchase Order %s approved and confirmed by Level 1 approver.",
                    self._get_html_link(title=self.name),
                )
                rec.message_post(
                    body=body)
            else:
                rec.state = 'approved_level1'
                rec._send_approval_notification('level2')
                body = _(
                    "Purchase Order %s approved at Level 1. Waiting for Level 2 approval.",
                    self._get_html_link(title=self.name),
                )
                rec.message_post(
                    body=body)
        return True

    def action_approve_level2(self):
        if not self.env.user.has_group('po_three_level_approval.group_po_approve_level2'):
            raise UserError(
                _("You don't have access to Level 2 approval."))
        now = fields.Datetime.now()
        for rec in self:
            rec.level2_approved_user_id = self.env.uid
            rec.level2_approved_date = now
            rec.button_approve()
            body = _(
                "Purchase Order %s approved and confirmed by Level 2 approver.",
                self._get_html_link(title=self.name),
            )
            rec.message_post(
                body=body)
        return True

    def _send_rejection_email(self, reason=None):
        self.ensure_one()
        template = self.env.ref(
            'po_three_level_approval.email_template_reject_purchase_order', raise_if_not_found=False)
        if not template:
            return

        email_to = self.create_uid.partner_id.email
        if not email_to:
            return

        template.send_mail(
            self.id, force_send=True, email_values={'email_to': email_to})

    def action_reject_approval(self):
        for rec in self:
            rec.rejected_uid = self.env.uid
            rec.state = 'rejected'
            rec._send_rejection_email()
