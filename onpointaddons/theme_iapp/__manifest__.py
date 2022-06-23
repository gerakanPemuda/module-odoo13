# -*- coding: utf-8 -*-
{
    'name': "Theme iApp",
	'category': 'Theme/Corporate',
	'version': '13.0',      
	'summary': 'Fully Responsive, Clean, Modern Latest Design Odoo Business Theme',
    'description': 'iApp Theme is a powerful one page Odoo theme designed for a Corporate or Agency Business design. It is a unique & clean Pixel Perfect Odoo theme Design with a creative modern look. Complete Design & all Sections very easy to customize and update using our new Snippets. It is built with various attractive features like one click installation, easy to change different Color Schemes, Many Custom Designed Snippets, Manage Slider with content, Manage Partner, Manage Portfolio, Client testimonial etc many more. It can be suitable for corporate businesses, Agency, IT Service, Construction, Health & Fitness etc any type of small business.',
    'license': 'OPL-1',
	'price': 39.99,
	'currency': 'EUR',
    'live_test_url': "http://207.180.228.60:8090/",
    'author': "Icon Technology",
    'website': "https://icontechnology.co.in",
    'support':  'team@icontechnology.in',
    'maintainer': 'Icon Technology',
    'images': [
        'static/description/iapp-v13.jpg',        
		'static/description/iapp_screenshot.gif'
	],
	
    # any module necessary for this one to work correctly
    'depends': ['website','website_crm','website_mass_mailing','product','website_blog','mail'],

    # always loaded
    'data': [
       'security/ir.model.access.csv',
       'data/website_crm_data.xml',
       'views/i_app_navbar_view.xml',
       'views/snnipets.xml',
       'views/website_template_view.xml',
       'views/website_blog_template.xml',
       'views/blog_detail_template.xml',
       'views/assets.xml',
       'views/view.xml'
    ],
    # only loaded in demonstration mode
    'demo': [
        'data/i_app_demo_data.xml',
    ],
    'application': True,
    'installable': True,
}