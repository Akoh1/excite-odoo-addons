openerp.ng_hr_payroll = function(instance) {
    var QWeb = instance.web.qweb;
    var _t = instance.web._t;

instance.web.form.FieldBinary.include({
    on_save_as: function(ev) {
        console.log('this.namethis.namethis.namethis.name',this.name);
        var value = this.get('value');
        var a = this.get('name')
        console.log('OkKOKOKOKOKOKK',name);
        if (!value) {
            this.do_warn(_t("Save As..."), _t("The field is empty, there's nothing to save !"));
            ev.stopPropagation();
        } else {
            instance.web.blockUI();
            var c = instance.webclient.crashmanager;
            this.session.get_file({
                url: '/custom_dload/saveas_ajax',
                data: {data: JSON.stringify({
                    model: this.view.dataset.model,
                    id: (this.view.datarecord.id || ''),
                    field: this.name,
                    filename_field: (this.view.datarecord.name || ''),/*this.node.attrs.filename*/
                    data: instance.web.form.is_bin_size(value) ? null : value,
                    context: this.view.dataset.get_context()
                })},
                complete: instance.web.unblockUI,
                error: c.rpc_error.bind(c)
            });
            ev.stopPropagation();
            return false;
        }
    },
    
    
});
};
