# -*- coding: utf-8 -*-
import time
import odoo.addons.decimal_precision as dp
from datetime import datetime
from odoo import models, fields, api
from odoo.tools.translate import _
from odoo.exceptions import UserError, ValidationError


class WizardStockInternalTransfer(models.TransientModel):
    _name = 'wizard.stock.internal.transfer'

    transfer_id = fields.Many2one('stock.internal.transfer', string="Transfer")
    item_ids = fields.One2many('stock.internal.transfer.items', 'transfer_id', string="Items")

    @api.model
    def default_get(self, fields):
        if self._context is None:
            self._context = {}
        res = super(WizardStockInternalTransfer, self).default_get(fields)
        transfer_ids = self._context.get('active_ids', [])
        active_model = self._context.get('active_model')

        if not transfer_ids or len(transfer_ids) != 1:
            return res

        assert active_model in ('stock.internal.transfer', 'Bad context propagation')
        transfer_id, = transfer_ids
        transfers = self.env['stock.internal.transfer'].browse(transfer_id)

        company_id = self.env['res.users'].browse(self._uid).company_id.id
        company = self.env['res.company'].browse(company_id)

        items = []

        if not company.transit_location_id:
            raise UserError(_("Please setup your stock transit location in Setting - Internal Transfer Configuration"))

        if transfers.state == 'draft':
            source_location_id = transfers.source_warehouse_id.lot_stock_id.id
            dest_location_id = company.transit_location_id.id
        elif transfers.state == 'send':
            source_location_id = company.transit_location_id.id
            dest_location_id = transfers.dest_warehouse_id.lot_stock_id.id

        for transfer in transfers.line_ids:
            item = {
                'product_id': transfer.product_id.id,
                'product_uom_id': transfer.product_uom_id.id,
                'product_qty': transfer.product_qty,
                'source_location_id': source_location_id,
                'dest_location_id': dest_location_id
            }
            if transfer.product_id:
                items.append(item)

        res.update(item_ids=items)
        return res

    def button_confirm(self):
        type_obj = self.env['stock.picking.type']
        picking_obj = self.env['stock.picking']
        move_obj = self.env['stock.move']

        for tf in self:
            if 'active_ids' in self._context:
                transfer = self.env['stock.internal.transfer'].browse(self._context.get('active_ids')[0])
                company_id = self.env['res.users'].browse(self._uid).company_id.id
                company = self.env['res.company'].browse(company_id)

                if transfer.state == 'draft':
                    backorders, user_list = [], []
                    user_ids = transfer.source_warehouse_id.user_ids
                    if user_ids:
                        for user in user_ids:
                            user_list.append(user.id)

                    if self._uid not in user_list:
                        raise UserError(_('You are not authorized to send or receive products !'))

                    for line in tf.item_ids:
                        for trans in transfer.line_ids:
                            if line.product_id.id == trans.product_id.id:
                                if line.product_qty > trans.product_qty:
                                    raise UserError(_('You have exceed the available product quantity.'))
                                elif line.product_qty < trans.product_qty:
                                    backorders.append({
                                        'product_id': line.product_id.id,
                                        'product_qty': trans.product_qty - line.product_qty,
                                        'product_uom_id': line.product_uom_id.id,
                                        'state': 'draft',
                                    })

                                    self.env['stock.internal.transfer.line'].write(trans.id,
                                                                                   {'product_qty': line.product_qty})

                    if backorders:
                        create_id = self.env['stock.internal.transfer'].create({
                            'date': time.strftime('%Y-%m-%d %H:%M:%S'),
                            'source_location_id': transfer.source_location_id.id,
                            'dest_location_id': transfer.dest_location_id.id,
                            'backorder_id': self._context.get('active_ids')[0],
                            'state': 'draft',
                        })
                        for backorder in backorders:
                            backorder['transfer_id'] = create_id
                            self.env['stock.internal.transfer.line'].create(backorder)

                    types = type_obj.search(
                        [('default_location_src_id', '=', transfer.source_warehouse_id.lot_stock_id.id),
                         ('code', '=', 'outgoing')], limit=1)

                    if types:
                        picking_id = picking_obj.create({
                            'picking_type_id': types.id,
                            'transfer_id': self._context.get('active_ids')[0],
                            'location_id': transfer.source_warehouse_id.lot_stock_id.id,
                            'location_dest_id': company.transit_location_id.id,
                            'company_id': types.company_id.id,
                        })
                    else:
                        raise UserError(_('Unable to find source location in Stock Picking'))

                    for line in tf.item_ids:
                        move_obj.create({
                            'name': 'Stock Internal Transfer',
                            'product_id': line.product_id.id,
                            'product_uom': line.product_uom_id.id,
                            'product_uom_qty': line.product_qty,
                            'location_id': line.source_location_id.id,
                            'location_dest_id': line.dest_location_id.id,
                            'picking_id': picking_id.id,
                            'company_id': types.company_id.id,
                        })

                    picking_id.action_confirm()
                    picking_id.action_assign()
                    picking_id.button_validate()

                    immediate_transfer = self.env['stock.immediate.transfer'].create({
                        'pick_ids': [(4, p.id) for p in picking_id],
                        'show_transfers': False,
                    })
                    immediate_transfer.process()
                    picking_id.state = 'done'

                    # picking_obj = self.env['stock.picking'].browse(picking_id.id)
                    # # picking_obj.action_confirm()
                    # # picking_obj.action_assign()
                    # # picking_obj.button_validate()
                    # immediate_transfer_obj = self.env['stock.immediate.transfer'].search(
                    #     [('pick_ids', '=', picking_id.id)])
                    # immediate_transfer_obj.process()
                    # picking_obj.action_done()
                    transfer.state = 'send'

                elif transfer.state == 'send':
                    backorders = []
                    user_list = []
                    user_ids = transfer.dest_warehouse_id.user_ids
                    if user_ids:
                        for user in user_ids:
                            user_list.append(user.id)

                    if self._uid not in user_list:
                        raise UserError(_('You are not authorized to send or receive product !'))

                    for line in tf.item_ids:
                        for trans in transfer.line_ids:
                            if line.product_id.id == trans.product_id.id:
                                if line.product_qty > trans.product_qty:
                                    raise UserError(_('You have exceed the available product quantity'))
                                elif line.product_qty < trans.product_qty:
                                    backorder = {
                                        'product_id': line.product_id.id,
                                        'product_qty': trans.product_qty - line.product_qty,
                                        'product_uom_id': line.product_uom_id.id,
                                        'state': 'draft',
                                    }
                                    backorders.append(backorder)

                    if backorders:
                        create_id = self.env['stock.internal.transfer'].create({
                            'date': time.strftime('%Y-%m-%d %H:%M:%S'),
                            'source_location_id': transfer.source_location_id.id,
                            'dest_location_id': transfer.dest_location_id.id,
                            'backorder_id': self._context.get('active_ids')[0],
                            'state': 'send',
                        })
                        for backorder in backorders:
                            backorder['transfer_id'] = create_id
                            self.env['stock.internal.transfer.line'].create(backorder)
                        # wkf_service.trg_validate('stock.internal.transfer', create_id, 'action_send')

                    types = type_obj.search(
                        [('default_location_dest_id', '=', transfer.dest_warehouse_id.lot_stock_id.id),
                         ('code', '=', 'incoming')], limit=1)

                    if types:
                        picking_id = picking_obj.create({
                            'picking_type_id': types.id,
                            'transfer_id': self._context.get('active_ids')[0],
                            'location_id': company.transit_location_id.id,
                            'location_dest_id': transfer.dest_warehouse_id.lot_stock_id.id,
                            'company_id': types.company_id.id,
                        })
                    else:
                        raise UserError(_('Unable to find destination location in Stock Picking'))

                    for line in tf.item_ids:
                        move_obj.create({
                            'name': 'Stock Internal Transfer',
                            'product_id': line.product_id.id,
                            'product_uom': line.product_uom_id.id,
                            'product_uom_qty': line.product_qty,
                            'location_id': line.source_location_id.id,
                            'location_dest_id': line.dest_location_id.id,
                            'picking_id': picking_id.id,
                            'company_id': types.company_id.id,
                        })

                    picking_id.action_confirm()
                    picking_id.action_assign()
                    picking_id.button_validate()

                    immediate_transfer = self.env['stock.immediate.transfer'].create({
                        'pick_ids': [(4, p.id) for p in picking_id],
                        'show_transfers': False,
                    })
                    immediate_transfer.process()
                    picking_id.state = 'done'

                    # picking_obj = self.env['stock.picking'].browse(picking_id.id)
                    # picking_obj.action_confirm()
                    # picking_obj.action_assign()
                    # picking_obj.button_validate()
                    #
                    # immediate_transfer_obj = self.env['stock.immediate.transfer'].search(
                    #     [('pick_ids', '=', picking_obj.id)])
                    # immediate_transfer_obj.process()
                    # picking_obj.action_done()
                    transfer.state = 'done'

        return True

    def wizard_view(self, created_id):
        view = self.env.ref('sgeede_internal_transfer.wizard_stock_internal_transfer_view')
        # active_model = self.env.context.get('active_model')
        return {
            'name': _('Enter Transfer Details'),
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'wizard.stock.internal.transfer',
            'views': [(view.id, 'form')],
            'view_id': view.id,
            'target': 'new',
            'res_id': created_id,
            'context': self.env.context
        }


class StockInternalTransferItems(models.TransientModel):
    _name = "stock.internal.transfer.items"

    transfer_id = fields.Many2one('wizard.stock.internal.transfer', string="Transfer")
    product_id = fields.Many2one('product.product', string="Product")
    product_qty = fields.Float(string="Quantity")
    product_uom_id = fields.Many2one('uom.uom', string="Unit of Measure")
    source_location_id = fields.Many2one('stock.location', string="Source Location")
    transit_location_id = fields.Many2one('stock.location', string="Transit Location")
    dest_location_id = fields.Many2one('stock.location', string="Destination Location")

    @api.onchange('product_id')
    def product_id_change(self):
        result = {}
        if not self.product_id:
            return {'value': {'product_uom_id': False}}

        product = self.env['product.product'].browse(self.product_id.id)
        product_uom_id = product.uom_id and product.uom_id.id or False
        result['value'] = {'product_uom_id': product_uom_id}
        return result
