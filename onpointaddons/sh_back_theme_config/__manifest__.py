# -*- coding: utf-8 -*-
# Part of Softhealer Technologies.
{
    "name" :   "Backmate Configuration Base",
    "author" : "Softhealer Technologies",
    "website": "https://www.softhealer.com",
    "support": "support@softhealer.com",    
    "category": "Extra Tools",
    "summary": "Backmate configuration base comes in Backmate Backend Theme Basics depends only.",
    "description": """
Are you bored with your standard odoo backend theme? Are You are looking for modern, creative, clean, clear, materialize Odoo theme for your backend? So you are at right place, We have made sure that this theme is highly customizable and it comes with a premium look and feel. Our theme is not only beautifully designed but also fully functional, flexible, fast, lightweight, animated and modern multipurpose theme. Our backend theme is suitable for almost every purpose.
    
                    """,      
    "version":"13.0.4",
    "depends" : [
                    "base",
                      
                ],
    "application" : True,
    "data" : [
        
            "security/ir.model.access.csv",
            "data/theme_config_data.xml",
            "views/back_theme_config_view.xml",
            "views/assets_backend.xml",
            "wizard/theme_preview_wizard.xml",
            
            ],            
    "images": ["static/description/background.png",],              
    "auto_install": False,
    "installable" : True,
    "price": 10,
    "currency": "EUR"   
}
