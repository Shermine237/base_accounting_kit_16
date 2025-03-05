# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2019-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
#
#    You can modify it under the terms of the GNU LESSER
#    GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################
from odoo import models, fields, _
from odoo.exceptions import UserError


class AccountRegisterPayments(models.TransientModel):
    _inherit = "account.payment.register"

    bank_reference = fields.Char(copy=False)
    cheque_reference = fields.Char(copy=False)
    effective_date = fields.Date('Effective Date',
                               help='Effective date of PDC', copy=False,
                               default=False)

    def _create_payment_vals_from_wizard(self, batch_result):
        payment_vals = super()._create_payment_vals_from_wizard(batch_result)
        # Check payment method is Check or PDC
        check_pdc_ids = self.env['account.payment.method'].search([('code', 'in', ['pdc', 'check_printing'])])
        if self.payment_method_id.id in check_pdc_ids.ids:
            currency_id = self.env['res.currency'].browse(payment_vals['currency_id'])
            journal_id = self.env['account.journal'].browse(payment_vals['journal_id'])
            payment_vals.update({
                'bank_reference': self.bank_reference,
                'cheque_reference': self.cheque_reference,
                'check_manual_sequencing': journal_id.check_manual_sequencing,
                'effective_date': self.effective_date,
                'check_amount_in_words': currency_id.amount_to_text(payment_vals['amount']),
            })
        return payment_vals


class AccountPayment(models.Model):
    _inherit = "account.payment"

    bank_reference = fields.Char(copy=False)
    cheque_reference = fields.Char(copy=False)
    effective_date = fields.Date('Effective Date',
                               help='Effective date of PDC', copy=False,
                               default=False)

    def action_post(self):
        """ Overridden to handle PDC effective date """
        res = super().action_post()
        inbound_pdc_id = self.env.ref(
            'base_accounting_kit_16.account_payment_method_pdc_in').id
        outbound_pdc_id = self.env.ref(
            'base_accounting_kit_16.account_payment_method_pdc_out').id
        
        for payment in self:
            if (payment.payment_method_id.id in [inbound_pdc_id, outbound_pdc_id] 
                and payment.effective_date):
                for move in payment.move_id:
                    move.date = payment.effective_date
                    for line in move.line_ids:
                        line.date_maturity = payment.effective_date
        return res

    def print_checks(self):
        """ Check that the recordset is valid, set the payments state to
        sent and call print_checks() """
        # Since this method can be called via a client_action_multi, we
        # need to make sure the received records are what we expect
        self = self.filtered(lambda r:
                           r.payment_method_id.code
                           in ['check_printing', 'pdc']
                           and r.state != 'posted')
        if len(self) == 0:
            raise UserError(_(
                "Payments to print as checks must have 'Check' "
                "or 'PDC' selected as payment method and "
                "not have already been posted"))
        if any(payment.journal_id != self[0].journal_id for payment in self):
            raise UserError(_(
                "In order to print multiple checks at once, they "
                "must belong to the same bank journal."))

        if not self[0].journal_id.check_manual_sequencing:
            # The wizard asks for the number printed on the first
            # pre-printed check so payments are attributed the
            # number of the check they'll be printed on.
            last_printed_check = self.search([
                ('journal_id', '=', self[0].journal_id.id),
                ('check_number', '!=', "0")], order="check_number desc",
                limit=1)
            next_check_number = last_printed_check and int(
                last_printed_check.check_number) + 1 or 1
            return {
                'name': _('Print Pre-numbered Checks'),
                'type': 'ir.actions.act_window',
                'res_model': 'print.prenumbered.checks',
                'view_mode': 'form',
                'target': 'new',
                'context': {
                    'payment_ids': self.ids,
                    'default_next_check_number': next_check_number,
                }
            }
        else:
            self.filtered(lambda r: r.state == 'draft').action_post()
            return self.do_print_checks()
