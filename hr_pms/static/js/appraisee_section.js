odoo.define('hr_pms.appraisee_section', function (require) {
    "use strict";

    var core = require('web.core');
    var session = require('web.session');
    var FormView = require('web.FormView');

    FormView.include({
        render_buttons: function ($node) {
            this._super.apply(this, arguments);

            if (this.model == 'pms.appraisee') {
                var self = this;
                var isAppraisee = false;

                // Replace 'employee_id' with the actual field name
                var employeeId = this.datarecord['employee_id'][0];

                // Fetch 'user_id' for the logged-in user
                var userId = session.uid;

                // Compare 'employee_id.user_id' with the logged-in user
                if (employeeId === userId) {
                    isAppraisee = true;
                }

                // Set the 'is_appraisee' variable in the template
                this.$buttons.find('.o_form_buttons_edit').prop('disabled', !isAppraisee);
                this.$el.find('.o_form_buttons_edit').prop('disabled', !isAppraisee);

                self.is_appraisee = isAppraisee;
                self.render_buttons();

                self.trigger_up('web_client_notification', {
                    type: 'success',
                    title: 'Visibility Set',
                    message: 'Field visibility has been set based on the user.'
                });
            }
        },
    });
});
