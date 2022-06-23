# -*- coding: utf-8 -*-
#################################################################################
# Author      : OnpointDevTeam
# Copyright(c): 2020
# All Rights Reserved.
#
#
#
# This program is copyright property of the author mentioned above.
# You can`t redistribute it and/or modify it.
#
#
# You should have received a copy of the License along with this program.
#################################################################################
{
    "name": "Onpoint Dashboard Application",
    "summary": "",
    "category": "Dashboard",
    "version": "1.0",
    "sequence": 1,
    "author": "OnpointDevTeam",
    "license": "Other proprietary",
    "website": "",
    "description": "",
    "live_test_url": "",
    "depends": [
        'web_google_maps',
        'onpoint_monitor',
    ],
    "data": [
        # 'views/main_templates.xml',
        'views/onpoint_dashboard_assets_backend.xml',
        'views/onpoint_dashboard_menu.xml',
    ],
    'qweb': [
        'static/src/xml/main_dashboard_templates.xml',
        'static/src/xml/mimic_dashboard_templates.xml',
    ],
    "images": [],
    "application": True,
    "installable": True,
    "auto_install": False,
}
