odoo.define('sh_backmate_theme.menu', function (require) {
"use strict";


var core = require('web.core');
var AppsMenu = require("web.AppsMenu");
var config = require("web.config");
var Menu = require("web.Menu");
var FormRenderer = require('web.FormRenderer');

// Responsive view "action" buttons
FormRenderer.include({

    /**
     * In mobiles, put all statusbar buttons in a dropdown.
     *
     * @override
     */
    _renderHeaderButtons: function () {
        var $buttons = this._super.apply(this, arguments);
        if (
            !config.device.isMobile ||
            !$buttons.is(":has(>:not(.o_invisible_modifier))")
        ) {
            return $buttons;
        }

        // $buttons must be appended by JS because all events are bound
        $buttons.addClass("dropdown-menu");
        var $dropdown = $(core.qweb.render(
            'sh_backmate_theme.MenuStatusbarButtons'
        ));
        $buttons.addClass("dropdown-menu").appendTo($dropdown);
        return $dropdown;
    },
});


var RelationalFields = require('web.relational_fields');

RelationalFields.FieldStatus.include({

    /**
     * Fold all on mobiles.
     *
     * @override
     */
    _setState: function () {
        this._super.apply(this, arguments);
        if (config.device.isMobile) {
            _.map(this.status_information, function (value) {
                value.fold = true;
            });
        }
    },
});




Menu.include({
    events: _.extend({
        // Clicking a hamburger menu item should close the hamburger
        "click .o_menu_sections [role=menuitem]": "_hideMobileSubmenus",
        // Opening any dropdown in the navbar should hide the hamburger
        "show.bs.dropdown .o_menu_systray, .o_menu_apps":
            "_hideMobileSubmenus",
    }, Menu.prototype.events),

    start: function () {
        this.$menu_toggle = this.$(".o-menu-toggle");
        return this._super.apply(this, arguments);
    },

    /**
     * Hide menus for current app if you're in mobile
     */
    _hideMobileSubmenus: function () {
        if (
            this.$menu_toggle.is(":visible") &&
            this.$section_placeholder.is(":visible")
        ) {
            this.$section_placeholder.collapse("hide");
        }
    },

    /**
     * No menu brand in mobiles
     *
     * @override
     */
    _updateMenuBrand: function () {
        if (!config.device.isMobile) {
            return this._super.apply(this, arguments);
        }
    },
});









});
