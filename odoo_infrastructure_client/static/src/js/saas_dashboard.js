odoo.define('saas_client', function (require) {
"use strict";

var Widget = require('web.Widget');
var Dashboard = require('web_settings_dashboard');


var DashboardSaaS = Widget.extend({

    template: 'DashboardSaaS',

    init: function(parent, data){
        this.data = data;
        this.parent = parent;
        return this._super.apply(this, arguments);
    },

});

Dashboard.Dashboard.include({
    init: function(parent, data){
        var ret = this._super(parent, data);
        this.all_dashboards.push('saas');
        return ret;
    },
    load_saas: function(data){
        return new DashboardSaaS(
        this, data.saas).replace(this.$('.o_web_settings_dashboard_saas'));
    },
});

});
