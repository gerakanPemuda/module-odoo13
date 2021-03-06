odoo.define('web_google_maps.relational_fields', function (require) {
    
    var core = require('web.core');
    var relational_fields = require('web.relational_fields');
    var MapRenderer = require('web_google_maps.MapRenderer');

    var qweb = core.qweb;

    relational_fields.FieldOne2Many.include({
        _render: function () {
            if (!this.view || this.renderer) {
                return this._super();
            }
            var arch = this.view.arch;
            if (arch.tag == 'google_map') {
                if (!arch.mode) {
                    throw new Error('View google_map: mode is undefined!');
                }
                this.renderer = this['_render_map_' + arch.mode]();
                this.$el.addClass('o_field_x2many o_field_x2many_google_map');
                return this.renderer.appendTo(this.$el);
            }
            return this._super();
        },
        _render_map_geometry: function (arch) {
            var record_options = {
                editable: true,
                deletable: true,
                read_only_mode: this.isReadonly
            }
            return new MapRenderer(this, this.value, {
                arch: arch,
                record_options: record_options,
                viewType: 'google_map',
                fieldLat: arch.attrs.lat,
                fieldLng: arch.attrs.lng,
                markerColor: arch.attrs.color,
                mapMode: arch.attrs.mode,
            });
        },
        /**
         * Override
         */
        _renderButtons: function () {
            this._super.apply(this, arguments);
            if (this.view.arch.tag === 'google_map') {
                this['_render_map_button_' + this.view.arch.mode]();
            }
        },
        _render_map_button_geometry: function() {
            var options = {create_text: this.nodeOptions.create_text, widget: this};
            this.$buttons = $(qweb.render('MapView.buttons', options));
            this.$buttons.on('click', 'button.o-map-button-new', this._onAddRecord.bind(this));
            this.$buttons.on('click', 'button.o-map-button-center-map', this._onMapCenter.bind(this));
        },
        _onMapCenter: function (event) {
            event.stopPropagation();
            this['_map_center_' + this.renderer.mapMode]();
        }
    });

});