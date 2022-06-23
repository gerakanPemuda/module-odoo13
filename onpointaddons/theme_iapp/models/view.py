from odoo import api, fields, models,SUPERUSER_ID,_
from odoo.modules.loading import force_demo
import odoo
import logging
import threading
import odoo.tools as tools
from odoo.exceptions import UserError, ValidationError
_logger = logging.getLogger(__name__)


class Screenshort(models.Model):
    _name = "screen.short"
    _description = "Screen short Slider"
    
    image = fields.Binary("Logos", attachment=True)
    filename = fields.Char(string="File Name")
    
class CustomerReview(models.Model):
    _name = "customer.review"
    _description = "Testimonial"
    
    partner_id = fields.Many2one('res.partner', string="Customer")
    review = fields.Text(string="Review")
    image = fields.Binary("Image",related='partner_id.image_1920')

class ProductTemplate(models.Model):
    _inherit = 'product.template'
    
    analyzer = fields.Char(string="Analyzer")
    support = fields.Char(string="Support")
    session = fields.Char(string="Sessions")
    no_risk = fields.Char(string="No Risk") 
    show_product = fields.Boolean(string="Active Product", default=False)
    mo = fields.Char(string="MO")
    

class BlogPost(models.Model):
    _inherit = "blog.post"
    
    cover_blog = fields.Boolean(string="Active Grid Bolg", default=False)
    popular_blog = fields.Boolean(string="Active Popular Bolg", default=False)
    blog_ids = fields.Many2many('blog.blog', string='Blog Category')
    
class BlogTag(models.Model):
    _inherit = 'blog.tag'
    
    show_tag = fields.Boolean(string="Active Tag", default=False)
    

class Blog(models.Model):
    _inherit = 'blog.blog'
    
    show_category = fields.Boolean(string="Active Category", default=False)
    
class MailMessage(models.Model):
    _inherit = 'mail.message'
    
    name = fields.Char(string="Name")
    email_id = fields.Char(string="Email")
    
class WebsiteContactInfo(models.Model):
    _name ="website.contact.info"
    _description = "Website Contact Information"
    
    name = fields.Char("Name")
    email = fields.Char("Email")
    subject = fields.Char("Subject")
    question = fields.Text("Message")
    
 
class LoadDemo(models.TransientModel):

    _name = 'load.demo'
    _description = 'Load Demo'

    def install_demo(self):
        force_demo_custom(self,self.env.cr)
        return {
            'type': 'ir.actions.act_url',
            'target': 'self',
            'url': '/web',
        }        

# bese default method odoo demo data Oading Demo Data
def load_data(cr, idref, mode, kind, package, report):
    """

    kind: data, demo, test, init_xml, update_xml, demo_xml.

    noupdate is False, unless it is demo data or it is csv data in
    init mode.

    """
    def _get_files_of_kind(kind):
        if kind == 'demo':
            kind = ['demo_xml', 'demo']
        elif kind == 'data':
            kind = ['init_xml', 'update_xml', 'data']
        if isinstance(kind, str):
            kind = [kind]
        files = []
        for k in kind:
            for f in package.data[k]:
                files.append(f)
                if k.endswith('_xml') and not (k == 'init_xml' and not f.endswith('.xml')):
                    # init_xml, update_xml and demo_xml are deprecated except
                    # for the case of init_xml with csv and sql files as
                    # we can't specify noupdate for those file.
                    correct_key = 'demo' if k.count('demo') else 'data'
                    _logger.warning(
                        "module %s: key '%s' is deprecated in favor of '%s' for file '%s'.",
                        package.name, k, correct_key, f
                    )
        return files

    try:
        if kind in ('demo', 'test'):
            threading.currentThread().testing = True
        for filename in _get_files_of_kind(kind):
            _logger.info("loading %s/%s", package.name, filename)
            noupdate = False
            if kind in ('demo', 'demo_xml') or (filename.endswith('.csv') and kind in ('init', 'init_xml')):
                noupdate = True
            tools.convert_file(cr, package.name, filename, idref, mode, noupdate, kind, report)
    finally:
        if kind in ('demo', 'test'):
            threading.currentThread().testing = False
            
# get the data xml file frommodule           
def load_demo_custom(cr, package, idref, mode, report=None):
    """
    Loads demo data for the specified package.
    """
#     if not package.should_have_demo():
#         return False
    try:
        _logger.info("Module %s: loading demo", package.name)
        with cr.savepoint(flush=False):
            load_data(cr, idref, mode, kind='demo', package=package, report=report)
        return True
    except Exception as e:
        # If we could not install demo data for this module
        _logger.warning(
            "Module %s demo data failed to install, installed without demo data",
            package.name, exc_info=True)

        env = api.Environment(cr, SUPERUSER_ID, {})
        todo = env.ref('base.demo_failure_todo', raise_if_not_found=False)
        Failure = env.get('ir.demo_failure')
        if todo and Failure is not None:
            todo.state = 'open'
            Failure.create({'module_id': package.id, 'error': str(e)})
        return False      
      
# custom method  to install demo data     
def force_demo_custom(self,cr):
    """
    Forces the `demo` flag on custom modules, and installs demo data for custom installed modules.
    """
    # get  custom module name if demo data not load
    ir_module_obj = self.env["ir.module.module"].search([('name','=','theme_iapp')])
    if ir_module_obj.demo == False:
        graph = odoo.modules.graph.Graph()
        cr.execute("UPDATE ir_module_module SET demo=True where name='theme_iapp'")
        cr.execute(
            "SELECT name FROM ir_module_module WHERE state IN ('installed', 'to upgrade', 'to remove')"
        )
        module_list = [name for (name,) in cr.fetchall()]
        graph.add_modules(cr, module_list, ['demo'])
        for package in graph:
            if package.name == 'theme_iapp':
                load_demo_custom(cr, package, {}, 'init')
        env = api.Environment(cr, SUPERUSER_ID, {})
        env['ir.module.module'].invalidate_cache(['demo'])
        
    # if demo data load install time that generate warning
    else:
        raise UserError(_("Already Install Demo Data."))
        