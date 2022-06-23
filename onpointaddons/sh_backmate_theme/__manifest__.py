# -*- coding: utf-8 -*-

{
    "name": "Backmate Backend Theme Basics",
    "author" : "Softhealer Technologies",
    "website": "https://www.softhealer.com",
    "support": "support@softhealer.com",
    "description": """
                Are you bored with your standard odoo backend theme? Are You are looking for modern, creative, clean, clear, materialize Odoo theme for your backend? So you are at right place, We have made sure that this theme is highly customizable and it comes with a premium look and feel. Our theme is not only beautifully designed but also fully functional, flexible, fast, lightweight, animated and modern multipurpose theme. Our backend theme is suitable for almost every purpose.
                """,
    "summary": "Backmate Backend Theme Basics is a fully functional, flexible, fast, lightweight, animated and modern multipurpose theme.",
    "category": "Theme/Backend",
    "version": "13.0.4",
    "depends":
    [
        "web",
        "sh_back_theme_config",
    ],
    
    "data":
    [
        "views/assets.xml",
        "views/login_layout.xml",
    ],

    "qweb": 
    [
        "static/src/xml/sh_thread.xml",
        "static/src/xml/menu.xml",    
        "static/src/xml/navbar.xml",    
        "static/src/xml/form_view.xml",
    ], 
    'images': [
        'static/description/splash-screen.gif',
        'static/description/splash-screen_screenshot.gif'
    ],
    "live_test_url": "https://softhealer.com/contact_us",   
    "installable": True,
    "application": True,
    "price": 60,
    "currency": "EUR",
    "bootstrap": True  
}    
