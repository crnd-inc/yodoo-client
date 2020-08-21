odoo.define('yodoo_client.db_expiry', function (require) {
    "use strict";

    var WebClient = require('web.WebClient');
    var ajax = require('web.ajax');
    var core = require('web.core');
    var qweb = core.qweb;

    ajax.loadXML('/yodoo_client/static/src/xml/db.xml', qweb);

    WebClient.include({
        start: function () {
            this.crnd_check_db_expiry();
            this._super.apply(this, arguments);
        },

        show_application: function () {
            var res = this._super.apply(this, arguments);
            this.crnd_click_db_expiry_ok();
            return res;
        },

        crnd_click_db_expiry_ok: function (message) {
            var accept_message_expiry = $("#accept_message_expiry");

            accept_message_expiry.click(function (e) {
                e.preventDefault();
                ajax.jsonRpc("/saas/client/db/expiry/accept", "call").then(function (data) {
                    if (data.result === "ok") {
                        $(e.target)
                            .closest("#yodoo-client-db-expiry")
                            .hide("fast");
                    }
                });
            });
        },

        crnd_check_db_expiry: function (message) {
            var self = this;
            var url = '/saas/client/db/state/get';
            ajax.jsonRpc(url).then(
                function (result) {
                    if (result) {
                        self.crnd_show_db_expiry(result);
                    }
                });
        },

        crnd_show_db_expiry: function (data) {
            var url = '/web/webclient/version_info';
            ajax.jsonRpc(url).then(
                function (result) {
                    if (result) {
                        if (result.server_version_info[0] === 11) {
                            var m = $('.o_main_content');
                        } else if (result.server_version_info[0] === 12) {
                            var m = $('.o_main_content');
                        } else if (result.server_version_info[0] === 13) {
                            var m = $('.o_action');
                        }
                        var t = $(qweb.render('yodoo_client.db.expiry', data));
                        m.prepend(t);
                    }
                });
        },
    });
});
