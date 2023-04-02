
from odoo import fields, models ,api, _
from tempfile import TemporaryFile
from odoo.exceptions import UserError, ValidationError, RedirectWarning
import base64
import random
import logging
from datetime import date, datetime, timedelta
from dateutil.relativedelta import relativedelta as rd
import xlrd
from xlrd import open_workbook
import base64

_logger = logging.getLogger(__name__)


class ImportRecords(models.TransientModel):
    _name = 'hr.import_record.wizard'

    data_file = fields.Binary(string="Upload File (.xls)")
    filename = fields.Char("Filename")
    index = fields.Integer("Sheet Index", default=0)
    import_type = fields.Selection([
            ('employee', 'Employee'),
            ('update', 'Update'),
        ],
        string='Import Type', required=True, index=True,
        copy=True, default='',
        track_visibility='onchange'
    )
 
    # def excel_reader(self, index=0):
    #     if self.data_file:
    #         file_datas = base64.decodestring(self.data_file)
    #         workbook = xlrd.open_workbook(file_contents=file_datas)
    #         sheet = workbook.sheet_by_index(index)
    #         data = [[sheet.cell_value(r, c) for c in range(sheet.ncols)] for r in range(sheet.nrows)]
    #         data.pop(0)
    #         file_data = data
    #         return file_data
    #     else:
    #         raise ValidationError('Please select file and type of file')
    
    def create_department(self, name):
        department_obj = self.env['hr.department']
        if name:
            depart_rec = department_obj.search([('name', '=', name.strip())], limit = 1)
            department_id = department_obj.create({
                        "name": name
                    }).id if not depart_rec else depart_rec.id
            return department_id
        else:
            return None

    def get_level_id(self, name):
        if not name:
            return False
        levelId = self.env['hr.level'].search([('name', '=', name)], limit=1)
        return levelId.id if levelId else self.env['hr.level'].create({'name': name}).id
    
    def get_district_id(self, name):
        if not name:
            return False
        rec = self.env['hr.district'].search([('name', '=', name)], limit=1)
        return rec.id if rec else self.env['hr.district'].create({'name': name}).id

    def get_grade_id(self, name):
        if not name:
            return False
        gradeId = self.env['hr.grade'].search([('name', '=', name)], limit=1)
        return gradeId.id if gradeId else self.env['hr.grade'].create({'name': name}).id
    
    def get_designation_id(self, name):
        if not name:
            return False
        designationId = self.env['hr.job'].search([('name', '=', name)], limit=1)
        return designationId.id if designationId else self.env['hr.job'].create({'name': name}).id

    def get_unit_id(self, name):
        if not name:
            return False
        rec = self.env['hr.unit'].search([('name', '=', name)], limit=1)
        return rec.id if rec else self.env['hr.unit'].create({'name': name}).id

    def get_sub_unit_id(self, name):
        if not name:
            return False
        rec = self.env['hr.work.unit'].search([('name', '=', name)], limit=1)
        return rec.id if rec else self.env['hr.work.unit'].create({'name': name}).id

    def import_records_action(self):
        if self.data_file:
            file_datas = base64.decodestring(self.data_file)
            workbook = xlrd.open_workbook(file_contents=file_datas)
            sheet = workbook.sheet_by_index(0)
            data = [[sheet.cell_value(r, c) for c in range(sheet.ncols)] for r in range(sheet.nrows)]
            data.pop(0)
            file_data = data
        else:
            raise ValidationError('Please select file and type of file')
        errors = ['The Following messages occurred']
        employee_obj = self.env['hr.employee']
        unimport_count, count = 0, 0
        success_records = []
        unsuccess_records = []
        
        def find_existing_employee(code):
            employee_id = False 
            if code:
                code = str(int(code)) if type(code) == float else code 
                employee = self.env['hr.employee'].search([
                    '|', ('employee_number', '=', code), 
                    ('barcode', '=', code)], limit = 1)
                if employee:
                    employee_id = employee.id
                else:
                    employee_id = False 
            return employee_id
        
        # reviewer_group = self.env.ref("hr_pms.group_pms_reviewer")
        # officer_group = self.env.ref("hr_pms.group_pms_officer_id")
        # supervisor_group = self.env.ref("hr_pms.group_pms_supervisor")
        # manager_group = self.env.ref("hr_pms.group_pms_manager_id")
        def generate_emp_appraiser(employee, appraiser_code, type):
            appraiser = self.env['hr.employee'].search([
                '|', ('employee_number', '=', appraiser_code), 
                ('barcode', '=', appraiser_code)], limit = 1)
            emp_group = self.env.ref("hr_pms.group_pms_user_id")
            reviewer_group = self.env.ref("hr_pms.group_pms_reviewer")
            supervisor_group = self.env.ref("hr_pms.group_pms_supervisor")
            if appraiser and employee:
                if type == "ar":
                    employee.sudo().write({
                        'administrative_supervisor_id': appraiser.id
                        })
                    # raise ValidationError("this is the AR ======>{} and {} with".format(appraiser.name, employee.name, employee.administrative_supervisor_id.name))
                    group_list = [(6, 0, [emp_group.id, supervisor_group.id])]
                    appraiser.user_id.sudo().write({'groups_id':group_list})

                if type == "fr":
                    group_list = [(6, 0, [emp_group.id, supervisor_group.id])]
                    employee.sudo().write({
                        'parent_id': appraiser.id
                    })
                    appraiser.user_id.sudo().write({'groups_id':group_list})

                if type == "rr":
                    group_list = [(6, 0, [emp_group.id, supervisor_group.id, reviewer_group.id])]
                    # employee.reviewer_id = appraiser.id
                    employee.sudo().update({
                        'reviewer_id': appraiser.id
                    })
                    appraiser.user_id.sudo().write({'groups_id':group_list})

        def create_employee(vals):
            user, password = generate_user(vals)
            employee_id = self.env['hr.employee'].sudo().create({
                        'name': vals.get('fullname'),
                        'employee_number': vals.get('staff_number'),
                        'employee_identification_code': vals.get('staff_number'),
                        'ps_district_id': vals.get('district'),
                        'gender': vals.get('gender'),
                        'department_id': vals.get('department_id'),
                        'unit_id': vals.get('unit_id'),
                        'work_unit_id': vals.get('sub_unit_id'),
                        'employment_date': vals.get('employment_date'),
                        'grade_id': vals.get('grade_id'),
                        'level_id': vals.get('level_id'),
                        # 'administrative_supervisor_id': vals.get('administrative_supervisor_id'),
                        # 'parent_id': vals.get('functional_appraiser_id'),
                        # 'reviewer_id': vals.get('functional_reviewer_id'),
                        'work_email': vals.get('email'),
                        'private_email': vals.get('private_email'),
                        'work_phone': vals.get('work_phone'),
                        'mobile_phone': vals.get('work_phone'),
                        'phone': vals.get('phone'),
                        'job_id': vals.get('job_id'),
                        'user_id': user.id,
                        'migrated_password': password,
                        # 'emergency_phone': vals.get('emergency_phone'),
                    })
            employee_id.sudo().write({
                                      'work_email': vals.get('email')
            })

        def generate_user(
                vals,
                ):
            emp_group = self.env.ref("hr_pms.group_pms_user_id")
            Group = self.env['res.groups'].sudo()
            group_list = [(4, emp_group.id)]
            ## Removing Contact Creation and Employee group from Org. relateduser.
            groups_to_remove = Group.search(
                ['|','|','|',
                 ('name', '=', 'Contact Creation'),
                 ('name','=','Portal'),
                 ('name','=','Manual Attendance'),
                 ('id', 'in', [
                self.env.ref('hr.group_hr_manager').id,
                self.env.ref('hr.group_hr_user').id,]),
                 ])
            for group in groups_to_remove:
                tup = (3,group.id)
                group_list.append(tup)
            email = vals.get('email') or vals.get('private_emaill')
            fullname = vals.get('fullname')
            if email:
                password = ''.join(random.choice('eedcpasswodforxyzusers1234567') for _ in range(10))
                # '{}-{}'.format(fullname[:2].upper(), str(uuid.uuid4())[:8]), # MA-2132ERER
                user_vals = {
				'name' : fullname,
				'login' : email,
				'password': password,
                }
                _logger.info("Creating employee Rep User...")
                User = self.env['res.users'].sudo()
                user = User.search([('login', '=', email)],limit=1)
                if user:
                    pass # user.write(user_vals)
                else:
                    user = User.create(user_vals)
                _logger.info('Adding user to group ...')
                user.sudo().write({'groups_id':group_list})
                return user, password
                     
        if self.import_type == "employee":
            for row in file_data:
                # try:
                appt_date = '01-Jan-2014'
                if row[14]:
                    pref = row[14].strip()[0:7] # 12-Jul-
                    suff = '20'+ row[14].strip()[-2:] # 2022
                    appt_date = pref + suff 
                vals = dict(
                    serial = row[0],
                    staff_number = str(int(row[1])),
                    fullname = row[2].capitalize(),
                    district = self.get_district_id(row[3].strip()),
                    level_id = self.get_level_id(row[5].strip()),
                    gender = 'male' if row[10] in ['m', 'M'] else 'female' if row[10] in ['f', 'F'] else 'other',
                    department_id = self.create_department(row[11]),
                    unit_id = self.get_unit_id(row[12].strip()),
                    sub_unit_id = self.get_sub_unit_id(row[13].strip()),
                    employment_date = datetime.strptime(appt_date, '%m-%b-%Y') if row[14].strip() else False,
                    # employment_date = datetime.strptime(row[14], '%m/%d/%Y') if row[14] else False,
                    grade_id = self.get_grade_id(row[15].strip()),
                    job_id = self.get_designation_id(row[16]),
                    functional_appraiser_id = find_existing_employee(row[18]),
                    administrative_supervisor_name = row[19],
                    administrative_supervisor_id = find_existing_employee(str(row[20])),
                    functional_reviewer_id = find_existing_employee(str(row[22])),
                    email = row[24].strip() or row[26].strip(),
                    private_email = row[26].strip(),
                    work_phone = row[25] or row[28] or 27,
                    phone = row[27] or row[25],
                    )
                create_employee(vals)
                count += 1
                success_records.append(vals.get('fullname'))
            errors.append('Successful Import(s): '+str(count)+' Record(s): See Records Below \n {}'.format(success_records))
            errors.append('Unsuccessful Import(s): '+str(unsuccess_records)+' Record(s)')
            if len(errors) > 1:
                message = '\n'.join(errors)
                return self.confirm_notification(message) 

        elif self.import_type == "update":
            for row in file_data:
                ########################### This is for update purposes:
                employee_code = str(int(row[1])) if type(row[1]) == float else row[1]
                appt_date = '01-Jan-2014'
                if row[14]:
                    pref = row[14].strip()[0:7] # 12-Jul-
                    suff = '20'+ row[14].strip()[-2:] # 2022
                    appt_date = pref + suff 
                employee_vals = dict(
                    employee_number = str(int(row[1])),
                    employee_identification_code = employee_code,
                    name = row[2].capitalize(),
                    ps_district_id = self.get_district_id(row[3].strip()),
                    level_id = self.get_level_id(row[5].strip()),
                    gender = 'male' if row[10] in ['m', 'M'] else 'female' if row[10] in ['f', 'F'] else 'other',
                    department_id = self.create_department(row[11]),
                    unit_id = self.get_unit_id(row[12].strip()),
                    work_unit_id = self.get_sub_unit_id(row[13].strip()),
                    employment_date = datetime.strptime(appt_date, '%m-%b-%Y') if row[14].strip() else False,
                    # employment_date = datetime.strptime(row[14], '%m/%d/%Y') if row[14] else False,
                    grade_id = self.get_grade_id(row[15].strip()),
                    job_id = self.get_designation_id(row[16]), 
                    work_email = row[24].strip() or row[26].strip(),
                    private_email = row[26].strip(),
                    work_phone = str(int(row[25])) if type(row[25]) in [float] else row[25] or str(int(row[28])) if type(row[28]) in [float] else row[28],
                    phone = str(int(row[27])) if type(row[27]) in [float] else row[25] or row[25],
                    )
                # ######################################
                # THIS IS TO UPDATE THE EMPLOYEE DEPARTMENTAL MANAGER AND APPRAISERS 
                aa, fa, rr = row[18],row[20],row[22]
                vals = dict(
                    staff_number = employee_code,
                    functional_appraiser_id = row[18],
                    administrative_supervisor_id = row[20],
                    functional_reviewer_id = row[22], 
                    )
                    ## if fa, add, fr get the employee id, add the 
                    ## attributes to employee, also update the femployee user
                    ## group with the groups
                employee_id = self.env['hr.employee'].search([
                '|', ('employee_number', '=', employee_code), 
                ('barcode', '=', employee_code)], limit = 1)
                if employee_id:
                    if aa:
                        administrative_supervisor_id = str(int(vals.get('administrative_supervisor_id'))) \
                        if type(row[20]) == float else row[20]
                        generate_emp_appraiser(
                            employee_id, 
                            administrative_supervisor_id, 
                            'ar', 
                            )
                    if fa:
                        functional_appraiser_id = str(int(vals.get('functional_appraiser_id'))) \
                        if type(row[18]) == float else row[18]
                        generate_emp_appraiser(
                            employee_id, 
                            functional_appraiser_id, 
                            'fr', 
                            )
                    if rr:
                        functional_reviewer_id = str(int(vals.get('functional_reviewer_id'))) \
                        if type(row[22]) == float else row[22]
                        generate_emp_appraiser(
                            employee_id, 
                            functional_reviewer_id,
                            'rr', 
                            )
                    employee_id.sudo().update(employee_vals)
                    count += 1
                else:
                    unsuccess_records.append(employee_code)
            errors.append('Successful Update(s): ' +str(count))
            errors.append('Unsuccessful Update(s): '+str(unsuccess_records)+' Record(s)')
            if len(errors) > 1:
                message = '\n'.join(errors)
                return self.confirm_notification(message) 
        
    def confirm_notification(self,popup_message):
        view = self.env.ref('migration_app.hr_migration_confirm_dialog_view')
        view_id = view and view.id or False
        context = dict(self._context or {})
        context['message'] = popup_message
        return {
                'name':'Message!',
                'type':'ir.actions.act_window',
                'view_type':'form',
                'res_model':'hr.migration.confirm.dialog',
                'views':[(view.id, 'form')],
                'view_id':view.id,
                'target':'new',
                'context':context,
                }


class MigrationDialogModel(models.TransientModel):
    _name="hr.migration.confirm.dialog"
    
    def get_default(self):
        if self.env.context.get("message", False):
            return self.env.context.get("message")
        return False 

    name = fields.Text(string="Message",readonly=True,default=get_default)

 