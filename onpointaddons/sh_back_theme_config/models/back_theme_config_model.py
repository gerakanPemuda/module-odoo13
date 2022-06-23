# -*- coding: utf-8 -*-
# Part of Softhealer Technologies.

from odoo import models, fields, api, _
import base64

dict_theme_style = {
    'style_1': {
        'primary_color': '#673AB7',
        'primary_hover': '#553098',
        'primary_active': '#553098',
        'secondary_color': '#e6e6e6',
        'secondary_hover': '#CDCDCD',
        'secondary_active': '#CDCDCD',
        'header_background_color': '#673AB7',
        'header_font_color': '#FFFFFF',
        'header_hover_color': '#553098',
        'header_active_color': '#553098',
        'h1_color': '#4E4E4E',
        'h2_color': '#4E4E4E',
        'h3_color': '#4E4E4E',
        'h4_color': '#4E4E4E',
        'h5_color': '#4E4E4E',
        'h6_color': '#4E4E4E',
        'p_color': '#4E4E4E',
        'h1_size': 28,
        'h2_size': 17,
        'h3_size': 18,
        'h4_size': 20,
        'h5_size': 13,
        'h6_size': 12,
        'p_size': 13,
        'body_font_color': '#4E4E4E',
        'body_background_color': '#F8F8F8',
        'body_font_family': 'custom_google_font',
        'button_style': 'style_2',
        'separator_style': 'style_2',
        'separator_color': '#9C27B0',
        'sidebar_background_color': '#FFFFFF',
        'sidebar_font_color': '#4E4E4E',
        'sidebar_font_hover_color': '#FFFFFF',
        'sidebar_font_hover_background_color': '#553098',
        'sidebar_style': 'style_2',
        'body_background_type': 'bg_color',
        'sidebar_background_type': 'bg_color',
        'is_button_with_icon_text': False,

        'body_google_font_family': 'Arimo',
        'is_used_google_font': True,

        'list_view_border': 'without_border',
        'list_view_is_hover_row': True,
        'list_view_hover_bg_color': '#ccc',
        'list_view_even_row_color': '#FFFFFF',
        'list_view_odd_row_color': '#FFFFFF',

        'login_page_style': 'style_0',
        'login_page_background_type': 'bg_color',
        'login_page_background_color': '#B3FFB8',
        'login_page_box_color': False,

    },

    'style_2': {
        'primary_color': '#2196F3',
        'primary_hover': '#1C80D0',
        'primary_active': '#1C80D0',
        'secondary_color': '#E6E6E6',
        'secondary_hover': '#CDCDCD',
        'secondary_active': '#CDCDCD',
        'header_background_color': '#2196F3',
        'header_font_color': '#FFFFFF',
        'header_hover_color': '#1C80D0',
        'header_active_color': '#1C80D0',
        'h1_color': '#4E4E4E',
        'h2_color': '#4E4E4E',
        'h3_color': '#4E4E4E',
        'h4_color': '#4E4E4E',
        'h5_color': '#4E4E4E',
        'h6_color': '#4E4E4E',
        'p_color': '#4E4E4E',
        'h1_size': 28,
        'h2_size': 17,
        'h3_size': 18,
        'h4_size': 20,
        'h5_size': 13,
        'h6_size': 12,
        'p_size': 13,
        'body_font_color': '#4E4E4E',
        'body_background_color': '#f9f9f9',
        'body_font_family': 'Raleway',
        'button_style': 'style_1',
        'separator_style': 'style_1',
        'separator_color': '#3F51B5',
        'sidebar_background_color': '#FFFFFF',
        'sidebar_font_color': '#4E4E4E',
        'sidebar_font_hover_color': '#FFFFFF',
        'sidebar_font_hover_background_color': '#1C80D0',
        'sidebar_style': 'style_1',
        'body_background_type': 'bg_color',
        'sidebar_background_type': 'bg_color',
        'is_button_with_icon_text': False,
        'body_google_font_family': False,
        'is_used_google_font': False,

        'list_view_border': 'without_border',
        'list_view_is_hover_row': True,
        'list_view_hover_bg_color': '#dedede',
        'list_view_even_row_color': '#FFFFFF',
        'list_view_odd_row_color': '#f5f5f5',

        'login_page_style': 'style_0',
        'login_page_background_type': 'bg_color',
        'login_page_background_color': '#B3FFB8',
        'login_page_box_color': False,

    },

    'style_3': {
        'primary_color': '#720d5d',
        'primary_hover': '#5d1049',
        'primary_active': '#5d1049',
        'secondary_color': '#E6E6E6',
        'secondary_hover': '#CDCDCD',
        'secondary_active': '#CDCDCD',
        'header_background_color': '#720d5d',
        'header_font_color': '#FFFFFF',
        'header_hover_color': '#5d1049',
        'header_active_color': '#5d1049',
        'h1_color': '#4E4E4E',
        'h2_color': '#4E4E4E',
        'h3_color': '#4E4E4E',
        'h4_color': '#4E4E4E',
        'h5_color': '#4E4E4E',
        'h6_color': '#4E4E4E',
        'p_color': '#4E4E4E',
        'h1_size': 28,
        'h2_size': 17,
        'h3_size': 18,
        'h4_size': 20,
        'h5_size': 13,
        'h6_size': 12,
        'p_size': 13,
        'body_font_color': '#4E4E4E',
        'body_background_color': '#F9F9F9',
        'body_font_family': 'Poppins',
        'button_style': 'style_3',
        'separator_style': 'style_3',
        'separator_color': '#5D1049',
        'sidebar_background_color': '#FFFFFF',
        'sidebar_font_color': '#FFFFFF',
        'sidebar_font_hover_color': '#FFFFFF',
        'sidebar_font_hover_background_color': '#5D1049',
        'sidebar_style': 'style_3',
        'body_background_type': 'bg_color',
        'sidebar_background_type': 'bg_img',
        'is_button_with_icon_text': True,

        'body_google_font_family': False,
        'is_used_google_font': False,

        'list_view_border': 'bordered',
        'list_view_is_hover_row': True,
        'list_view_hover_bg_color': '#dadada',
        'list_view_even_row_color': '#FFFFFF',
        'list_view_odd_row_color': '#FFFFFF',

        'login_page_style': 'style_0',
        'login_page_background_type': 'bg_color',
        'login_page_background_color': '#B3FFB8',
        'login_page_box_color': False,

    },

    'style_4': {
        'primary_color': '#4A6572',
        'primary_hover': '#344955',
        'primary_active': '#344955',
        'secondary_color': '#E6E6E6',
        'secondary_hover': '#CDCDCD',
        'secondary_active': '#CDCDCD',
        'header_background_color': '#4A6572',
        'header_font_color': '#FFFFFF',
        'header_hover_color': '#344955',
        'header_active_color': '#344955',
        'h1_color': '#4E4E4E',
        'h2_color': '#4E4E4E',
        'h3_color': '#4E4E4E',
        'h4_color': '#4E4E4E',
        'h5_color': '#4E4E4E',
        'h6_color': '#4E4E4E',
        'p_color': '#4E4E4E',
        'h1_size': 28,
        'h2_size': 17,
        'h3_size': 18,
        'h4_size': 20,
        'h5_size': 13,
        'h6_size': 12,
        'p_size': 13,
        'body_font_color': '#4E4E4E',
        'body_background_color': '#F9F9F9',
        'body_font_family': 'Oxygen',
        'button_style': 'style_4',
        'separator_style': 'style_4',
        'separator_color': '#344955',
        'sidebar_background_color': '#FFFFFF',
        'sidebar_font_color': '#4E4E4E',
        'sidebar_font_hover_color': '#FFFFFF',
        'sidebar_font_hover_background_color': '#344955',
        'sidebar_style': 'style_4',
        'body_background_type': 'bg_color',
        'sidebar_background_type': 'bg_color',
        'is_button_with_icon_text': False,

        'body_google_font_family': False,
        'is_used_google_font': False,

        'list_view_border': 'bordered',
        'list_view_is_hover_row': True,
        'list_view_hover_bg_color': '#dadada',
        'list_view_even_row_color': '#FFFFFF',
        'list_view_odd_row_color': '#f5f5f5',

        'login_page_style': 'style_0',
        'login_page_background_type': 'bg_color',
        'login_page_background_color': '#B3FFB8',
        'login_page_box_color': False,

    },

    'style_5': {
        'primary_color': '#43A047',
        'primary_hover': '#388E3C',
        'primary_active': '#388E3C',
        'secondary_color': '#E6E6E6',
        'secondary_hover': '#CDCDCD',
        'secondary_active': '#CDCDCD',
        'header_background_color': '#43A047',
        'header_font_color': '#FFFFFF',
        'header_hover_color': '#388E3C',
        'header_active_color': '#388E3C',
        'h1_color': '#4E4E4E',
        'h2_color': '#4E4E4E',
        'h3_color': '#4E4E4E',
        'h4_color': '#4E4E4E',
        'h5_color': '#4E4E4E',
        'h6_color': '#4E4E4E',
        'p_color': '#4E4E4E',
        'h1_size': 28,
        'h2_size': 17,
        'h3_size': 18,
        'h4_size': 20,
        'h5_size': 13,
        'h6_size': 12,
        'p_size': 13,
        'body_font_color': '#4E4E4E',
        'body_background_color': '#F9F9F9',
        'body_font_family': 'OpenSans',
        'button_style': 'style_5',
        'separator_style': 'style_5',
        'separator_color': '#388E3C',
        'sidebar_background_color': '#FFFFFF',
        'sidebar_font_color': '#4E4E4E',
        'sidebar_font_hover_color': '#FFFFFF',
        'sidebar_font_hover_background_color': '#388E3C',
        'sidebar_style': 'style_5',
        'body_background_type': 'bg_color',
        'sidebar_background_type': 'bg_color',
        'is_button_with_icon_text': False,

        'body_google_font_family': False,
        'is_used_google_font': False,

        'list_view_border': 'bordered',
        'list_view_is_hover_row': True,
        'list_view_hover_bg_color': '#dadada',
        'list_view_even_row_color': '#FFFFFF',
        'list_view_odd_row_color': '#f5f5f5',

        'login_page_style': 'style_0',
        'login_page_background_type': 'bg_color',
        'login_page_background_color': '#B3FFB8',
        'login_page_box_color': False,

    },

    'style_6': {
        'primary_color': '#C8385E',
        'primary_hover': '#AA2F50',
        'primary_active': '#AA2F50',
        'secondary_color': '#E6E6E6',
        'secondary_hover': '#CDCDCD',
        'secondary_active': '#CDCDCD',
        'header_background_color': '#C8385E',
        'header_font_color': '#FFFFFF',
        'header_hover_color': '#AA2F50',
        'header_active_color': '#AA2F50',
        'h1_color': '#4E4E4E',
        'h2_color': '#4E4E4E',
        'h3_color': '#4E4E4E',
        'h4_color': '#4E4E4E',
        'h5_color': '#4E4E4E',
        'h6_color': '#4E4E4E',
        'p_color': '#4E4E4E',
        'h1_size': 28,
        'h2_size': 17,
        'h3_size': 18,
        'h4_size': 20,
        'h5_size': 13,
        'h6_size': 12,
        'p_size': 13,
        'body_font_color': '#4E4E4E',
        'body_background_color': '#F9F9F9',
        'body_font_family': 'OpenSans',
        'button_style': 'style_5',
        'separator_style': 'style_5',
        'separator_color': '#AA2F50',
        'sidebar_background_color': '#FFFFFF',
        'sidebar_font_color': '#FFFFFF',
        'sidebar_font_hover_color': '#FFFFFF',
        'sidebar_font_hover_background_color': '#AA2F50',
        'sidebar_style': 'style_6',
        'body_background_type': 'bg_img',
        'sidebar_background_type': 'bg_img',
        'is_button_with_icon_text': True,

        'body_google_font_family': False,
        'is_used_google_font': False,

        'list_view_border': 'bordered',
        'list_view_is_hover_row': True,
        'list_view_hover_bg_color': '#dadada',
        'list_view_even_row_color': '#FFFFFF',
        'list_view_odd_row_color': '#f5f5f5',

        'login_page_style': 'style_0',
        'login_page_background_type': 'bg_color',
        'login_page_background_color': '#B3FFB8',
        'login_page_box_color': False,

    },

    'style_onpoint': {
        'primary_color': '#4e4e4e',
        'primary_hover': '#000000',
        'primary_active': '#9cb4a1',
        'secondary_color': '#ffffff',
        'secondary_hover': '#CDCDCD',
        'secondary_active': '#b8b6b6',
        'header_background_color': '#df1429',
        'header_font_color': '#FFFFFF',
        'header_hover_color': '#9cb4a1',
        'header_active_color': '#9cb4a1',
        'h1_color': '#000000',
        'h2_color': '#000000',
        'h3_color': '#000000',
        'h4_color': '#000000',
        'h5_color': '#000000',
        'h6_color': '#000000',
        'p_color': '#000000',
        'h1_size': 28,
        'h2_size': 17,
        'h3_size': 18,
        'h4_size': 20,
        'h5_size': 13,
        'h6_size': 12,
        'p_size': 13,
        'body_font_color': '#000000',
        'body_background_color': '#ced8d0',
        'body_font_family': 'Oxygen',
        'button_style': 'style_3',
        'separator_style': 'style_3',
        'separator_color': '#df1429',
        'sidebar_background_color': '#FFFFFF',
        'sidebar_font_color': '#FFFFFF',
        'sidebar_font_hover_color': '#FFFFFF',
        'sidebar_font_hover_background_color': '#df1429',
        'sidebar_style': 'style_3',
        'body_background_type': 'bg_color',
        'sidebar_background_type': 'bg_img',
        'is_button_with_icon_text': True,

        'body_google_font_family': False,
        'is_used_google_font': False,

        'list_view_border': 'bordered',
        'list_view_is_hover_row': True,
        'list_view_hover_bg_color': '#dadada',
        'list_view_even_row_color': '#FFFFFF',
        'list_view_odd_row_color': '#FFFFFF',

        'login_page_style': 'style_1',
        'login_page_background_type': 'bg_color',
        'login_page_background_color': '#9cb4a1',
        'login_page_box_color': '#ffffff',

    },

}


class sh_back_theme_config_settings(models.Model):
    _name = 'sh.back.theme.config.settings'
    _description = 'Back Theme Config Settings'

    name = fields.Char(string="Theme Settings")

    theme_style = fields.Selection([
        ('style_1', 'Style 1'),
        ('style_2', 'Style 2'),
        ('style_3', 'Style 3'),
        ('style_4', 'Style 4'),
        ('style_5', 'Style 5'),
        ('style_6', 'Style 6'),
        ('style_onpoint', 'Style Onpoint'),
    ], string="Theme Style")

    primary_color = fields.Char(string='Primary Color')
    primary_hover = fields.Char(string='Primary Hover')
    primary_active = fields.Char(string='Primary Active')

    secondary_color = fields.Char(string='Secondary Color')
    secondary_hover = fields.Char(string='Secondary Hover')
    secondary_active = fields.Char(string='Secondary Active')

    header_background_color = fields.Char(string='Header Background Color')
    header_font_color = fields.Char(string='Header Font Color')
    header_hover_color = fields.Char(string='Header Hover Color')
    header_active_color = fields.Char(string='Header Active Color')

    h1_color = fields.Char(string='H1 Color')
    h2_color = fields.Char(string='H2 Color')
    h3_color = fields.Char(string='H3 Color')
    h4_color = fields.Char(string='H4 Color')
    h5_color = fields.Char(string='H5 Color')
    h6_color = fields.Char(string='H6 Color')
    p_color = fields.Char(string='P Color')

    h1_size = fields.Integer(string='H1 Size')
    h2_size = fields.Integer(string='H2 Size')
    h3_size = fields.Integer(string='H3 Size')
    h4_size = fields.Integer(string='H4 Size')
    h5_size = fields.Integer(string='H5 Size')
    h6_size = fields.Integer(string='H6 Size')
    p_size = fields.Integer(string='P Size')

    body_font_color = fields.Char(string='Body Font Color')
    body_background_type = fields.Selection([
        ('bg_color', 'Color'),
        ('bg_img', 'Image')
    ], string="Body Background Type", default="bg_color")

    body_background_color = fields.Char(string='Body Background Color')
    body_background_image = fields.Binary(string='Body Background Image')
    body_font_family = fields.Selection([
        ('Roboto', 'Roboto'),
        ('Raleway', 'Raleway'),
        ('Poppins', 'Poppins'),
        ('Oxygen', 'Oxygen'),
        ('OpenSans', 'OpenSans'),
        ('KoHo', 'KoHo'),
        ('Ubuntu', 'Ubuntu'),
        ('custom_google_font', 'Custom Google Font'),
    ], string='Body Font Family')

    body_google_font_family = fields.Char(string="Google Font Family")
    is_used_google_font = fields.Boolean(string="Is use google font?")

    button_style = fields.Selection([
        ('style_1', 'Style 1'),
        ('style_2', 'Style 2'),
        ('style_3', 'Style 3'),
        ('style_4', 'Style 4'),
        ('style_5', 'Style 5'),
    ], string='Button Style')
    is_button_with_icon_text = fields.Boolean(string="Button with text and icon?")

    separator_style = fields.Selection([
        ('style_1', 'Style 1'),
        ('style_2', 'Style 2'),
        ('style_3', 'Style 3'),
        ('style_4', 'Style 4'),
        ('style_5', 'Style 5'),
    ], string='Separator Style')

    separator_color = fields.Char(string="Separator Color")

    sidebar_background_type = fields.Selection([
        ('bg_color', 'Color'),
        ('bg_img', 'Image')
    ], string="Sidebar Background Type", default="bg_color")

    sidebar_background_color = fields.Char(string='Sidebar Background Color')
    sidebar_background_image = fields.Binary(string='Sidebar Background Image')

    sidebar_font_color = fields.Char(string='Sidebar Font Color')
    sidebar_font_hover_color = fields.Char(string='Sidebar Font Hover Color')
    sidebar_font_hover_background_color = fields.Char(string='Sidebar Font Hover Background Color')
    sidebar_style = fields.Selection([
        ('style_1', 'Style 1'),
        ('style_2', 'Style 2'),
        ('style_3', 'Style 3'),
        ('style_4', 'Style 4'),
        ('style_5', 'Style 5'),
        ('style_6', 'Style 6'),
        ('style_7', 'Style 7'),
        ('style_8', 'Style 8'),
    ], string='Sidebar Style')

    loading_gif = fields.Binary(string="Loading GIF")
    loading_gif_file_name = fields.Char(string="Loading GIF File Name")

    list_view_border = fields.Selection([
        ('bordered', 'Bordered'),
        ('without_border', 'Without Border')
    ], default='without_border', string="List View Border")

    list_view_is_hover_row = fields.Boolean(string="Rows Hover?")
    list_view_hover_bg_color = fields.Char(string="Hover Background Color")
    list_view_even_row_color = fields.Char(string="Even Row Color")
    list_view_odd_row_color = fields.Char(string="Odd Row Color")

    login_page_style = fields.Selection([
        ('style_0', 'Odoo Standard'),
        ('style_1', 'Style 1'),
        ('style_2', 'Style 2'),
    ], default="style_0", string="Style")

    login_page_background_type = fields.Selection([
        ('bg_color', 'Color'),
        ('bg_img', 'Image')
    ], string="Background Type", default="bg_color")

    login_page_background_color = fields.Char(string='Background Color')
    login_page_background_image = fields.Binary(string='Background Image')
    login_page_box_color = fields.Char(string='Box Color')
    login_page_banner_image = fields.Char(string='Banner Image')

    # Sticky
    is_sticky_form = fields.Boolean(string="Form Status Bar")
    is_sticky_chatter = fields.Boolean(string="Chatter")
    is_sticky_list = fields.Boolean(string="List View")
    is_sticky_list_inside_form = fields.Boolean(string="List View Inside Form")

    @api.onchange('body_font_family')
    def onchage_body_font_family(self):
        if self.body_font_family == 'custom_google_font':
            self.is_used_google_font = True
        else:
            self.is_used_google_font = False
            self.body_google_font_family = False

    def action_preview_theme_style(self):
        if self:

            context = dict(self.env.context or {})
            img_src = ""
            if context and context.get('which_style', '') == 'theme':
                img_src = "/sh_back_theme_config/static/src/img/preview/theme/style_theme.png"

            if context and context.get('which_style', '') == 'button':
                img_src = "/sh_back_theme_config/static/src/img/preview/button/style_button.png"

            if context and context.get('which_style', '') == 'separator':
                img_src = "/sh_back_theme_config/static/src/img/preview/separator/style_separator.png"

            if context and context.get('which_style', '') == 'sidebar':
                img_src = "/sh_back_theme_config/static/src/img/preview/sidebar/style sidebar.png"

            if context and context.get('which_style', '') == 'login_page':
                img_src = "/sh_back_theme_config/static/src/img/preview/login_page/style_login.jpg"

            context['default_img_src'] = img_src

            return {
                'name': _('Preview Style'),
                'view_mode': 'form',
                'res_model': 'sh.theme.preview.wizard',
                'view_id': self.env.ref('sh_back_theme_config.sh_back_theme_config_theme_preview_wizard_form').id,
                'type': 'ir.actions.act_window',
                'context': context,
                'target': 'new',
                'flags': {'form': {'action_buttons': False}}
            }

    def action_change_theme_style(self):
        if self:
            return

    @api.onchange('theme_style')
    def onchage_theme_style(self):

        if self and self.theme_style:
            selected_theme_style_dict = dict_theme_style.get(self.theme_style, False)
            if selected_theme_style_dict:
                self.update(selected_theme_style_dict)

    def write(self, vals):
        """
           Write theme settings data in a less file
        """

        res = super(sh_back_theme_config_settings, self).write(vals)
        if self:
            for rec in self:

                content = """   
$o-enterprise-color: %s;
$primaryColor:%s;
$primary_hover:%s;
$primary_active:%s;
$secondaryColor:%s;
$secondary_hover:%s;
$secondary_active:%s;
$list_td_th:0.75rem !important;

$header_bg_color:%s;
$header_font_color:%s;
$header_hover_color:%s;
$header_active_color:%s;

$h1_color:%s;
$h2_color:%s;
$h3_color:%s;
$h4_color:%s;
$h5_color:%s;
$h6_color:%s;
$p_color:%s;

$h1_size:%spx;
$h2_size:%spx;
$h3_size:%spx;
$h4_size:%spx;
$h5_size:%spx;
$h6_size:%spx;
$p_size:%spx;

$body_font_color:%s;
$body_background_type:%s;
$body_background_color:%s;
$body_font_family:%s;

$button_style:%s;
$o-mail-attachment-image-size: 100px !default;


$sidebar_background_type:%s;
$sidebar_bg_color:%s;
$sidebar_font_color:%s;
$sidebar_font_hover_color:%s;
$sidebar_font_hover_bg_color:%s;
$sidebar_style:%s;

$separator_style:%s;
$separator_color:%s;

$o-community-color:%s;
$o-tooltip-background-color:%s;
$o-brand-secondary:%s;
$o-brand-odoo: $o-community-color;
$o-brand-primary: $o-community-color;

$is_button_with_icon_text:%s;

$body_google_font_family:%s;
$is_used_google_font:%s;

$list_view_border:%s;
$list_view_is_hover_row:%s;
$list_view_hover_bg_color:%s;
$list_view_even_row_color:%s;
$list_view_odd_row_color:%s;

$login_page_style: %s;
$login_page_background_type: %s;
$login_page_background_color:%s;
$login_page_box_color:%s;
$theme_style: %s;

$is_sticky_form:%s;
$is_sticky_chatter:%s;
$is_sticky_list:%s;
$is_sticky_list_inside_form:%s;

                """ % (

                    rec.primary_color,
                    rec.primary_color,
                    rec.primary_hover,
                    rec.primary_active,

                    rec.secondary_color,
                    rec.secondary_hover,
                    rec.secondary_active,

                    rec.header_background_color,
                    rec.header_font_color,
                    rec.header_hover_color,
                    rec.header_active_color,

                    rec.h1_color,
                    rec.h2_color,
                    rec.h3_color,
                    rec.h4_color,
                    rec.h5_color,
                    rec.h6_color,
                    rec.p_color,

                    rec.h1_size,
                    rec.h2_size,
                    rec.h3_size,
                    rec.h4_size,
                    rec.h5_size,
                    rec.h6_size,
                    rec.p_size,

                    rec.body_font_color,
                    rec.body_background_type,
                    rec.body_background_color,
                    rec.body_font_family,

                    rec.button_style,

                    rec.sidebar_background_type,
                    rec.sidebar_background_color,
                    rec.sidebar_font_color,
                    rec.sidebar_font_hover_color,
                    rec.sidebar_font_hover_background_color,
                    rec.sidebar_style,

                    rec.separator_style,
                    rec.separator_color,

                    rec.primary_color,
                    rec.primary_color,
                    rec.secondary_color,
                    rec.is_button_with_icon_text,

                    rec.body_google_font_family,
                    rec.is_used_google_font,

                    rec.list_view_border,
                    rec.list_view_is_hover_row,
                    rec.list_view_hover_bg_color,
                    rec.list_view_even_row_color,
                    rec.list_view_odd_row_color,

                    rec.login_page_style,
                    rec.login_page_background_type,
                    rec.login_page_background_color,
                    rec.login_page_box_color,
                    rec.theme_style,

                    rec.is_sticky_form,
                    rec.is_sticky_chatter,
                    rec.is_sticky_list,
                    rec.is_sticky_list_inside_form,

                )

                IrAttachment = self.env["ir.attachment"]
                # search default attachment by url that will created when app installed...
                url = "/sh_back_theme_config/static/src/scss/back_theme_config_main_scss.scss"

                search_attachment = IrAttachment.sudo().search([
                    ('url', '=', url),
                ], limit=1)

                # Check if the file to save had already been modified
                datas = base64.b64encode((content or "\n").encode("utf-8"))
                if search_attachment:
                    # If it was already modified, simply override the corresponding attachment content
                    search_attachment.sudo().write({"datas": datas})

                else:
                    # If not, create a new attachment
                    new_attach = {
                        "name": "Back Theme Settings scss File",
                        "type": "binary",
                        "mimetype": "text/scss",
                        "datas": datas,
                        "url": url,
                        "public": True,
                        "res_model": "ir.ui.view",
                    }

                    IrAttachment.sudo().create(new_attach)

                    # clear the catch to applied our new theme effects.
                self.env["ir.qweb"].clear_caches()

        return res
