from odoo import models, fields, api
from odoo.osv import expression


class PamCoaType(models.Model):
    _name = 'pam.coa.type'

    name = fields.Char(string='Nama', required=True)
    position = fields.Selection([
        ('debit', 'Debit'),
        ('credit', 'Credit')
    ], default='debit')
    coa_ids = fields.One2many('pam.coa', 'coa_type_id')


class PamCoaRef(models.Model):
    _name = 'pam.coa.ref'

    code = fields.Char(string="Kode Ref.", required=True)
    name = fields.Char(string='Nama', required=True)

    @api.model
    def name_search(self, name, args=None, operator='ilike', limit=100):
        args = args or []
        domain = []
        if name:
            domain = ['|', ('code', '=ilike', name + '%'), ('name', operator, name)]
            if operator in expression.NEGATIVE_TERM_OPERATORS:
                domain = ['&', '!'] + domain[1:]
        coa_ref = self.search(domain + args, limit=limit)
        return coa_ref.name_get()

    @api.depends('name', 'code')
    def name_get(self):
        result = []
        for coa_ref in self:
            name = coa_ref.code + ' - ' + coa_ref.name
            result.append((coa_ref.id, name))
        return result


class PamCoa(models.Model):
    _name = 'pam.coa'
    _rec_name = 'code'
    _order = "code"

    name = fields.Char(string='Nama', required=True)
    bank_name = fields.Char(string='Nama Bank')
    code = fields.Char(string='Kode', required=True)
    coa_type_id = fields.Many2one('pam.coa.type', string="Tipe", required=True, index=True)
    coa_type_name = fields.Char('pam.coa.type', related='coa_type_id.name')
    coa_ref_id = fields.Many2one('pam.coa.ref', string="Ref", index=True)
    transactional = fields.Boolean(string='Transaksional', index=True, default=True)
    parent_id = fields.Many2one('pam.coa', string='Group', ondelete='restrict', index=True)
    child_ids = fields.One2many('pam.coa', 'parent_id', string='Anggota')

    _parent_store = True
    parent_path = fields.Char(index=True)
    parent_left = fields.Integer(index=True)
    parent_right = fields.Integer(index=True)

    @api.constrains('parent_id')
    def _check_hierarchy(self):
        if not self._check_recursion():
            raise models.ValidationError('Error ! Anda tidak dapat menghubungkan ke diri sendiri')

    @api.model
    def name_search(self, name, args=None, operator='ilike', limit=100):
        args = args or []
        domain = []
        if name:
            domain = ['|', ('code', '=ilike', name + '%'), ('name', operator, name)]
            if operator in expression.NEGATIVE_TERM_OPERATORS:
                domain = ['&', '!'] + domain[1:]
        coa = self.search(domain + args, limit=limit)
        return coa.name_get()

    @api.depends('name', 'code')
    def name_get(self):
        result = []
        for coa in self:
            name = coa.code + ' - ' + coa.name
            result.append((coa.id, name))
        return result