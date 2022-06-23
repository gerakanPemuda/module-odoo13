from odoo import models, fields, api, _
from datetime import datetime
from dateutil.relativedelta import relativedelta
from odoo.exceptions import ValidationError


class OnpointWorkOrder(models.Model):
    _name = "onpoint.work.order"
    _inherit = ['image.mixin']

    name = fields.Char('No. Work Order')
    # state_id = fields.Many2one("res.country.state", string='State', ondelete='restrict', domain="[('country_id', '=?', country_id)]")
    # country_id = fields.Many2one('res.country', string='Country', ondelete='restrict')
    # city = fields.Char()
    street = fields.Char()
    logger_id = fields.Many2one('onpoint.logger', string='Logger')
    # street_name = fields.Char('Street Name', compute='_split_street',
    #                           inverse='_set_street', store=True)
    # street_number = fields.Char('House', compute='_split_street', help="House Number",
    #                             inverse='_set_street', store=True)
    # latitude = fields.Float(string='Geo Latitude', digits=(16, 5))
    # longitude = fields.Float(string='Geo Longitude', digits=(16, 5))
    work_time = fields.Integer(string='Duration', compute='_compute_work_time')
    work_time_uom = fields.Selection([
        ('minute', 'Minute'),
        ('hour', 'Hour'),
        ('day', 'Day'),
        ('month', 'Month'),
    ], string='Unit', compute='_compute_work_time')
    work_time_difference = fields.Integer(string='Difference', compute='_compute_work_time_difference')
    work_time_difference_uom = fields.Selection([
        ('minute', 'Minute'),
        ('hour', 'Hour'),
        ('day', 'Day'),
        ('month', 'Month'),
    ], string='Unit', compute='_compute_work_time_difference' )
    assign_to = fields.Many2one('hr.employee', string='Assign to')
    task = fields.Text('Remark')
    user_to_confirm_id = fields.Boolean(compute='get_user_to_confirm')
    user_to_accept_id = fields.Boolean(compute='get_user_to_accept')
    state = fields.Selection([
        ('draft', 'Draf'),
        ('submit', 'Submit'),
        ('confirm', 'Confirm'),
        ('en_route', 'En Route'),
        ('in_progress', 'In Progress'),
        ('pending', 'Pending'),
        ('complete', 'Complete'),
    ], 'State', default='draft')

    wo_type = fields.Many2one('onpoint.wo.type', str='WO Type', required=True)
    wo_type_pic_id = fields.Many2one(related='wo_type.pic_id')
    wo_type_pic_uid = fields.Integer(compute='get_user_to_confirm')
    wo_type_work_time = fields.Integer(related='wo_type.work_time')
    wo_type_work_time_uom = fields.Selection(related='wo_type.uom')
    wo_type_employee_ids = fields.Many2many('hr.employee', compute='_load_employees')
    wo_type_line_ids = fields.One2many(related='wo_type.line_ids')

    line_ids = fields.One2many('onpoint.work.order.line', 'wo_id')

    # @api.model
    # def _geo_localize(self, street='', city='', state='', country=''):
    #     geo_obj = self.env['base.geocoder']
    #     search = geo_obj.geo_query_address(street=street, city=city, state=state, country=country)
    #     result = geo_obj.geo_find(search, force_country=country)
    #     if result is None:
    #         search = geo_obj.geo_query_address(city=city, state=state, country=country)
    #         result = geo_obj.geo_find(search, force_country=country)
    #     return result
    #
    # def geo_localize(self):
    #     # We need country names in English below
    #     for partner in self.with_context(lang='en_US'):
    #         result = self._geo_localize(partner.street,
    #                                     partner.city,
    #                                     partner.state_id.name,
    #                                     partner.country_id.name)
    #
    #         if result:
    #             partner.write({
    #                 'latitude': result[0],
    #                 'longitude': result[1],
    #             })
    #     return True

    @api.depends('wo_type_pic_id')
    def get_user_to_confirm(self):
        for record in self:
            wo_type_pic_user_id = record.wo_type_pic_id.user_id
            record.wo_type_pic_uid =  record.wo_type_pic_id.user_id.id
            record.user_to_confirm_id = (True if wo_type_pic_user_id.id == record.env.user.id else False)

    @api.depends('assign_to')
    def get_user_to_accept(self):
        for record in self:
            teams = self._get_team_user_ids()
            record.user_to_accept_id = (True if record.env.user.id in teams else False)
            # assign_to_user_id = record.assign_to.user_id
            # record.user_to_accept_id = (True if assign_to_user_id.id == record.env.user.id else False)

    def _get_team_user_ids(self):
        employees = []
        if self.wo_type:
            employees.append(self.wo_type_pic_id.user_id.id)
            for wo_type_line in self.wo_type.line_ids:
                employees.append(wo_type_line.employee_id.user_id.id)

        return employees

    def _get_employees(self):
        employees = []
        if self.wo_type:
            for wo_type_line in self.wo_type.line_ids:
                employees.append(wo_type_line.employee_id.id)

        return employees


    @api.depends('wo_type')
    def _load_employees(self):
        self.wo_type_employee_ids = [(6, 0, self._get_employees())]

    @api.model
    def get_map_data(self):

        work_orders = self.env['onpoint.work.order'].sudo().search([])

        markers = []

        for work_order in work_orders:
            marker = {
                'id': work_order.id,
                'name': work_order.name,
                'wo_type': work_order.wo_type,
                'assign_to': work_order.assign_to,
                'work_time': work_order.work_time,
                'work_time_difference': work_order.work_time_difference,
                'position': {
                    'lat': work_order.latitude,
                    'lng': work_order.longitude
                },
            }

            markers.append(marker)

        data = {
            'markers': markers
        }

        return data

    def act_submit(self):
        self.line_ids.create({
            'wo_id': self.id,
            'state_from': 'draft',
            'state_to': 'submit',
        })

        sequence = self.env['ir.sequence'].next_by_code('onpoint.wo.sequence') or ''
        self.write({
            'state': 'submit',
            'name': sequence
        })

    def act_confirm(self):
        self.act_accept()
        # self.write({
        #     'state': 'confirm',
        # })

    def act_accept(self):
        wo_type = self.env['onpoint.wo.type'].search([('id', '=', self.wo_type.id)])
        wo_type_line = self.env['onpoint.wo.type.line'].search([('wo_type_id', '=', wo_type.id), ('employee_id', '=', self.assign_to.id)])
        wo_type_line.write({
            'state': 'not_available'
        })

        self.line_ids.create({
            'wo_id': self.id,
            'state_from': 'confirm',
            'state_to': 'in_progress'
        })

        self.write({
            'state': 'in_progress'
        })

    def act_reject(self):
        view_id = self.env.ref('onpoint_wo.view_onpoint_work_order_wizard_form').id

        return {
            'name': 'Work Order',
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'view_id': view_id,
            'res_model': 'onpoint.work.order.line',
            'target': 'new',
            'context': {
                'default_wo_id': self.id,
                'default_state_from': 'confirm',
                'default_state_to': 'submit',
            }
        }

    def act_progress(self):
        view_id = self.env.ref('onpoint_wo.view_onpoint_work_order_wizard_form').id

        return {
            'name': 'Work Order',
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'view_id': view_id,
            'res_model': 'onpoint.work.order.line',
            'target': 'new',
            'context': {
                'default_wo_id': self.id,
                'default_state_from': 'en_route',
                'default_state_to': 'in_progress',
            }
        }

    def act_pending(self):
        view_id = self.env.ref('onpoint_wo.view_onpoint_work_order_wizard_form').id

        return {
            'name': 'Work Order',
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'view_id': view_id,
            'res_model': 'onpoint.work.order.line',
            'target': 'new',
            'context': {
                'default_wo_id': self.id,
                'default_state_from': 'in_progress',
                'default_state_to': 'pending',
            }
        }

    def act_complete(self):
        view_id = self.env.ref('onpoint_wo.view_onpoint_work_order_wizard_form').id

        return {
            'name': 'Work Order',
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'view_id': view_id,
            'res_model': 'onpoint.work.order.line',
            'target': 'new',
            'context': {
                'default_wo_id': self.id,
                'default_state_from': 'in_progress',
                'default_state_to': 'complete',
            }
        }

    def _compute_work_time(self):
        for record in self:
            wo_lines = record.line_ids.filtered(lambda wo: wo.state_to == 'in_progress')
            domains = [('id', 'in', wo_lines.ids)]
            if wo_lines:
                durations = dict((line['wo_id'][0], line['duration']) for line in wo_lines.read_group(domains, ['wo_id', 'duration'], ['wo_id']))
                record.work_time = durations.get(record.id, 0.0)
                record.work_time_uom = 'minute'
            else:
                record.work_time = 0
                record.work_time_uom = ''

    def _compute_work_time_difference(self):
        for record in self:
            if record.work_time:
                # record.work_time_difference = (record.wo_type_work_time * 60) - record.work_time
                if record.wo_type_work_time_uom == 'hour':
                    wo_type_work_time_minute = record.wo_type_work_time * 60
                elif record.wo_type_work_time == 'day':
                    wo_type_work_time_minute = record.wo_type_work_time * 820
                else:
                    wo_type_work_time_minute = record.wo_type_work_time

                if wo_type_work_time_minute > record.work_time:
                    record.work_time_difference = 0
                    record.work_time_difference_uom = False

                else:
                    if wo_type_work_time_minute >= 820:
                        work_time_difference_day = (wo_type_work_time_minute - record.work_time) / 820
                        record.work_time_difference = work_time_difference_day
                        record.work_time_difference_uom = 'minute'
                    elif wo_type_work_time_minute >= 60:
                        record.work_time_difference = wo_type_work_time_minute - record.work_time
                        record.work_time_difference_uom = 'minute'
                    else:
                        record.work_time_difference = record.wo_type_work_time - record.work_time
                        record.work_time_difference_uom = 'minute'

            else:
                record.work_time_difference = False
                record.work_time_difference_uom = False


class OnpointWorkOrderLine(models.Model):
    _name = 'onpoint.work.order.line'
    _order = "create_date desc"
    _inherit = ['image.mixin']

    wo_id = fields.Many2one('onpoint.work.order', ondelete='cascade')
    state_from = fields.Selection([
        ('draft', 'Draf'),
        ('submit', 'Submit'),
        ('confirm', 'Confirm'),
        ('en_route', 'En Route'),
        ('in_progress', 'In Progress'),
        ('pending', 'Pending'),
        ('complete', 'Complete'),
    ], 'State From', default='draft')
    state_to = fields.Selection([
        ('draft', 'Draf'),
        ('submit', 'Submit'),
        ('confirm', 'Confirm'),
        ('en_route', 'En Route'),
        ('in_progress', 'In Progress'),
        ('pending', 'Pending'),
        ('complete', 'Complete'),
    ], 'State To', default='draft')
    duration = fields.Integer(string='Duration')
    remark = fields.Text('Notes')
    created_date = fields.Char(compute='compute_create_date')
    created_time = fields.Char(compute='compute_create_date')
    detail_ids = fields.One2many('onpoint.work.order.detail', 'wo_line_id')

    @api.depends('create_date')
    def compute_create_date(self):
        for record in self:
            if record.create_date:
                record.created_date = record.create_date.strftime('%d %b %Y')
                record.created_time = record.create_date.strftime('%H:%M')

    def open_form(self):
        view_id = self.env.ref('onpoint_wo.view_onpoint_work_order_line_form').id

        return {
            'name': 'Work Order',
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'view_id': view_id,
            'res_model': 'onpoint.work.order.line',
            'res_id': self.id,
            'target': 'current',
            'context': {
                'default_wo_id': self.wo_id.id,
                'default_create_date': self.create_date,
                'default_image_1920': self.image_1920,
                'default_state_from': self.state_from,
                'default_state_to': self.state_to,
                'default_duration': self.duration,
                'default_remark': self.remark,
            }
        }

    def add_comment(self):
        view_id = self.env.ref('onpoint_wo.view_onpoint_wo_comment_wizard_form').id

        return {
            'name': 'Work Order',
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'view_id': view_id,
            'res_model': 'onpoint.work.order.detail',
            'target': 'new',
            'context': {
                'default_wo_line_id': self.id
            }
        }

    def act_save(self):
        work_order = self.env['onpoint.work.order'].search([('id', '=', self.wo_id.id)])
        work_order.write({
            'state': self.state_to
        })
        return {
            'type': 'ir.actions.act_window_close'
        }

    def act_cancel(self):
        return {
            'type': 'ir.actions.act_window_close'
        }

    def getDuration(self, then, now=datetime.now(), interval="default"):
        duration = now - then
        duration_in_s = duration.total_seconds()

        def years():
            return divmod(duration_in_s, 31536000)  # Seconds in a year=31536000.

        def days(seconds=None):
            return divmod(seconds if seconds != None else duration_in_s, 86400)  # Seconds in a day = 86400

        def hours(seconds=None):
            return divmod(seconds if seconds != None else duration_in_s, 3600)  # Seconds in an hour = 3600

        def minutes(seconds=None):
            return divmod(seconds if seconds != None else duration_in_s, 60)  # Seconds in a minute = 60

        def seconds(seconds=None):
            if seconds != None:
                return divmod(seconds, 1)
            return duration_in_s

        def totalDuration():
            y = years()
            d = days(y[1])  # Use remainder to calculate next variable
            h = hours(d[1])
            m = minutes(h[1])
            s = seconds(m[1])

            return "Time between dates: {} years, {} days, {} hours, {} minutes and {} seconds".format(int(y[0]),
                                                                                                       int(d[0]),
                                                                                                       int(h[0]),
                                                                                                       int(m[0]),
                                                                                                       int(s[0]))

        return {
            'years': int(years()[0]),
            'days': int(days()[0]),
            'hours': int(hours()[0]),
            'minutes': int(minutes()[0]),
            'seconds': int(seconds()),
            'default': totalDuration()
        }[interval]

    # then = datetime(2012, 3, 5, 23, 8, 15)
    # now = datetime.now()
    #
    # print(getDuration(then))  # E.g. Time between dates: 7 years, 208 days, 21 hours, 19 minutes and 15 seconds
    # print(getDuration(then, now, 'years'))  # Prints duration in years
    # print(getDuration(then, now, 'days'))  # days
    # print(getDuration(then, now, 'hours'))  # hours
    # print(getDuration(then, now, 'minutes'))  # minutes
    # print(getDuration(then, now, 'seconds'))  # seconds

    def _compute_duration(self):
        for record in self:
            wo_line = self.env['onpoint.work.order.line'].search([('id', '>', record.id)], order='id asc', limit=1)

            then = record.create_date
            now = wo_line.create_date

            if now:
                record.duration = record.getDuration(then, now, 'minutes')
            else:
                record.duration = 0.0

    @api.model
    def create(self, values):
        res = super(OnpointWorkOrderLine, self).create(values)

        work_order_lines = self.env['onpoint.work.order.line'].search([('wo_id', '=', values['wo_id'])], order='create_date desc')

        previous_line = datetime.now()
        for work_order_line in work_order_lines:
            current_line = work_order_line.create_date
            duration = self.getDuration(current_line, previous_line, 'minutes')
            work_order_line.write({
                'duration': duration
            })
            previous_line = current_line

        work_order = self.env['onpoint.work.order'].search([('id', '=', res.wo_id.id)])
        work_order.write({
            'state': res.state_to
        })

        wo_id = self.env['onpoint.work.order'].search([('id', '=', res.wo_id.id)])
        if res.state_to == 'complete':
            wo_type = self.env['onpoint.wo.type'].search([('id', '=', wo_id.wo_type.id)])
            wo_type_line = self.env['onpoint.wo.type.line'].search([('wo_type_id', '=', wo_type.id), ('employee_id', '=', wo_id.assign_to.id)])
            wo_type_line.write({
                'state': 'available'
            })

        return res


class OnpointWorkOrderDetail(models.Model):
    _name = 'onpoint.work.order.detail'

    @api.model
    def _default_user(self):
        return self.env.context.get('user_id', self.env.user.id)

    wo_line_id = fields.Many2one('onpoint.work.order.line', ondelete='cascade')
    comment = fields.Text('Comment')
    user_id = fields.Many2one('res.users', string='User', default=_default_user)

    @api.model
    def create(self, values):
        res = super(OnpointWorkOrderDetail, self).create(values)

        return res
