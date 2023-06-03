from datetime import datetime, timedelta
from odoo import models, fields, api, _, SUPERUSER_ID
from odoo.exceptions import ValidationError, UserError
import logging
import xlrd
from xlrd import open_workbook
import base64

_logger = logging.getLogger(__name__)


class Post_Normalisation_Wizard(models.Model):
    _name = "pms.post_normalisation.wizard"

    data_file = fields.Binary(string="Upload File (.xls)")
    filename = fields.Char("Filename")
    index = fields.Integer("Sheet Index", default=0)
    uploader_id = fields.Many2one(
        'res.users',
        string='Requested by', 
        default=lambda self: self.env.uid,
        )


    def post_normalisation_action(self):
        if self.data_file:
            file_datas = base64.decodestring(self.data_file)
            workbook = xlrd.open_workbook(file_contents=file_datas)
            sheet_index = int(self.index) if self.index else 0
            sheet = workbook.sheet_by_index(sheet_index)
            data = [[sheet.cell_value(r, c) for c in range(sheet.ncols)] for r in range(sheet.nrows)]
            data.pop(0)
            file_data = data
        else:
            raise ValidationError('Please select file and type of file')
        unimport_count, count = 0, 0
        success_records = []
        unsuccess_records = []
        message = ['The Status of Post Normalisation Upload']
        # popup_message = 'The following staff ids were normalized:\n'

        def find_appraisal(code):
            employee_id = False 
            if code:
                code = str(int(code)) if type(code) == float else code 
                appraisal = self.env['pms.appraisee'].search([
                    '&', ('employee_number', '=', code),
                    ('state', '=', 'signed')], limit = 1)
                # raise ValidationError(appraisal.job_title)
                if appraisal:
                    return appraisal
                else:
                    return False
        
        for row in file_data:
            employee_appraisal = find_appraisal(row[1])
            if employee_appraisal:
                employee_appraisal.post_normalization_score = row[2]
                employee_appraisal.post_normalization_description = row[3]
                employee_appraisal.normalized_score_uploader_id = self.env.uid
                success_records.append(row[1])
                count += 1

        message.append('Successful upload(s): '+str(count)+' Appraisal Record(s): See Record ids below \n {}'.format(success_records))
        popup_message = '\n'.join(message)
        view = self.env.ref('hr_pms.pms_post_normalisation_confirm_dialog_view')
        view_id = view and view.id or False
        context = dict(self._context or {})
        context['message'] = popup_message
        return {
                'name':'Message!',
                'type':'ir.actions.act_window',
                'view_type':'form',
                'res_model':'pms.post_normalisation.confirm.dialog',
                'views':[(view.id, 'form')],
                'view_id':view.id,
                'target':'new',
                'context':context,
                }
        
class PostNormalisationDialogModel(models.TransientModel):
    _name="pms.post_normalisation.confirm.dialog"
    
    def get_default(self):
        if self.env.context.get("message", False):
            return self.env.context.get("message")
        return False 

    name = fields.Text(string="Message",readonly=True,default=get_default)