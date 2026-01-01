from odoo import models, fields, api
from odoo.exceptions import ValidationError
from odoo.tools import date_utils
from datetime import datetime, timedelta

class PerformanceAnalysis(models.Model):
	_name = 'performance.analysis'
	_description = 'Performance Analysis'
	_inherit = ['mail.thread', 'mail.activity.mixin']
	_rec_name = 'employee_id'
	
	employee_id = fields.Many2one('hr.employee', string='Employee', required=True,tracking=True)
	department_id = fields.Many2one('hr.department', string='Department',related='employee_id.department_id',tracking=True)
	state = fields.Selection([
		('draft', 'Draft'),
		('done', 'Done')
	], string='Status', default='draft', tracking=True)
	date_from = fields.Date(string="Date From", required=True,tracking=True)
	date_to = fields.Date(string="Date To", required=True,tracking=True)
	task_line_ids = fields.One2many(
		'performance.analysis.task.line',
		'analysis_id',
		string="Tasks"
	,tracking=True)	
	total_internal_hours = fields.Float(
		string="Total Internal Hours",
		compute="_compute_totals",
		store=True
	,tracking=True)
	total_client_hours = fields.Float(
		string="Total Client Hours",
		compute="_compute_totals",
		store=True,tracking=True
	)
	
	task_count = fields.Integer(string='Task Count', compute='_compute_timesheet_data', store=True)
	

	performance_lines = fields.One2many('performance.line', 'analysis_id', string='Performance Lines')
	weekly_summary = fields.One2many(
	'performance.summary', 
	'analysis_id', 
	string='Weekly Summary', 
)
	monthly_performance = fields.One2many('performance.monthly', 'analysis_id', string='Monthly Performance',
	  )
	state = fields.Selection([('draft', 'Draft'), ('done', 'Done')], string='Status', default='draft', tracking=True)

	@api.constrains('performance_lines')
	def _check_max_performance_lines(self):
		for record in self:
			if len(record.performance_lines) > 4:
				raise ValidationError("You can only create 4 Performance Factor lines (one per week).")

	def unlink(self):
			for record in self:
				if record.state == 'done':
					raise ValidationError("Cannot delete a record in 'Done' state.")
			return super(PerformanceAnalysis, self).unlink()

	def action_set_done(self):
		for record in self:
			if record.state != 'draft':
				raise ValidationError("Only Draft records can be marked as Done.")
			if record.date_from > record.date_to:
				raise ValidationError("From Date must be before To Date.")
			record.write({'state': 'done'})
			record.message_post(body="Performance evaluation marked as Done.")

	@api.depends('employee_id', 'date_from', 'date_to')
	def _compute_timesheet_data(self):
		for record in self:
			if not record.employee_id or not record.date_from or not record.date_to or not record._origin.id:
				record.total_hours = 0.0
				record.internal_hours = 0.0
				record.client_hours = 0.0
				record.task_count = 0
				record.department_id = False
				continue
			start_date = fields.Date.from_string(record.date_from)
			end_date = fields.Date.from_string(record.date_to)
			timesheet_lines = self.env['account.analytic.line'].search([
				('employee_id', '=', record.employee_id.id),
				('date', '>=', start_date),
				('date', '<=', end_date),
			])
			record.total_hours = sum(line.unit_amount for line in timesheet_lines)
			record.task_count = len(timesheet_lines)
			record.internal_hours = sum(line.unit_amount for line in timesheet_lines if not line.project_id)
			record.client_hours = sum(line.unit_amount for line in timesheet_lines if line.project_id)
			record.department_id = record.employee_id.department_id if record.employee_id.department_id else False


	@api.constrains('employee_id', 'date_from', 'date_to')
	def _check_date_overlap(self):
		for record in self:
			if record.date_from and record.date_to:
				overlapping = self.search([
					('id', '!=', record.id),
					('employee_id', '=', record.employee_id.id),
					('date_from', '<=', record.date_to),
					('date_to', '>=', record.date_from),
				])
				if overlapping:
					raise ValidationError(
						"A performance analysis for this employee already exists within the selected date range."
					)

	@api.depends('task_line_ids.internal_hours', 'employee_id', 'date_from', 'date_to')
	def _compute_totals(self):
		for rec in self:
			rec.total_internal_hours = sum(rec.task_line_ids.mapped('internal_hours'))
			if rec.employee_id and rec.date_from and rec.date_to:
				timesheets = self.env['account.analytic.line'].search([
					('employee_id', '=', rec.employee_id.id),
					('date', '>=', rec.date_from),
					('date', '<=', rec.date_to),
				])
				rec.total_client_hours = sum(timesheets.mapped('unit_amount'))
			else:
				rec.total_client_hours = 0.0

	fetch_done = fields.Boolean(default=False)
	fetch_Ts_done = fields.Boolean(default=False)
	
	weekly_summ = fields.Boolean(default=False)
	monthly_summ = fields.Boolean(default=False)


	def action_fetch_tasks(self):
		self.fetch_done = True

		for rec in self:
			if not rec.employee_id or not rec.date_from or not rec.date_to:
				continue

			# clear old lines
			rec.task_line_ids.unlink()

			# get tasks where user_id == employee's related user
			user = rec.employee_id.user_id
			if not user:
				continue

			tasks = self.env['project.task'].search([
				('user_id', '=', user.id),
				('create_date', '>=', rec.date_from),
				('create_date', '<=', rec.date_to),
			])

			lines = []
			for task in tasks:
				lines.append((0, 0, {
					'project_id': task.project_id.id,
					'task_id': task.id,
					'stage_id': task.stage_id.id,
					'internal_hours': task.effective_hours,   # adjust field
					'total_internal_hours': task.planned_hours,        # adjust field
				}))
			rec.task_line_ids = lines


	def action_draft(self):
		self.write({'state': 'draft'})

	def action_done(self):
		self.write({'state': 'done'})

	timesheet_line_ids = fields.One2many('performance.analysis.timesheet','analysis_id',string="Timesheet Lines")

	def action_fetch_timesheets(self):
		"""Fetch timesheets for this employee in the date range"""
		self.fetch_Ts_done = True

		self.ensure_one()
		if self.timesheet_line_ids:
			return  # Already fetched

		domain = [
			('employee_id', '=', self.employee_id.id),
			('date', '>=', self.date_from),
			('date', '<=', self.date_to),
		]
		timesheets = self.env['account.analytic.line'].search(domain)

		lines = []
		for ts in timesheets:
			lines.append((0, 0, {
				'date': ts.date,
				'name': ts.name,
				'unit_amount': ts.unit_amount,
				'task_id': ts.task_id.id,
				'project_id': ts.project_id.id,
			}))
		self.write({'timesheet_line_ids': lines})

	
	def action_calculate_weekly_summary(self):
		self.weekly_summ = True
		for record in self:
			if record.weekly_summary:
				record.weekly_summary.unlink()

			lines = record.performance_lines.sorted(key=lambda l: l.start_date_new or fields.Date.today())
			if not lines:
				continue

			# assume 4 lines = 4 weeks
			for i in range(4):
				line = lines[i] if i < len(lines) else None
				if not line:
					continue
				performance_score = record._calculate_performance_score(line)
				print(performance_score)
				self.env['performance.summary'].create({
					'analysis_id': record.id,
					'week_number': f'Week {i + 1}',
					'manager_review': line.manager_review,
					'hr_review': line.hr_review,
					'comments': line.comments,
					'performance_score_weekly': performance_score,
				})


	def action_calculate_monthly_performance(self):
		self.monthly_summ = True
		for record in self:
			if record.monthly_performance:
				record.monthly_performance.unlink()

			if record.weekly_summary:
				avg_score = sum(line.performance_score_weekly for line in record.weekly_summary) / len(record.weekly_summary)
				monthly_score = avg_score * 4   # out of 20
				monthly_data = {
					'analysis_id': record.id,
					'employee_name': record.employee_id.name,
					
					'performance_score_monthly': monthly_score,
				}
				self.env['performance.monthly'].create(monthly_data)


	def _calculate_performance_score(self, line):
		if not line:
			return 0.0
		fields_to_average = [
			'submit_timesheets', 'productivity', 'work_quality', 'consistency',
			'communication_skills', 'punctuality', 'client_relations', 'coworker_relations',
			'responsibility', 'leadership_skills', 'technical_skills',
			'daily_meeting_participation', 'hr_policy_compliance'
		]
		values = [getattr(line, f) or 0.0 for f in fields_to_average]
		return sum(values) / len(values) if values else 0.0

	@api.model
	def generate_performance_records(self):
		employees = self.env['hr.employee'].search([])
		today = fields.Date.today()
		for employee in employees:
			start_date = date_utils.start_of(today, 'week')
			end_date = date_utils.end_of(today, 'week')
			record = self.create({
				'employee_id': employee.id,
				'date_from': start_date,
				'date_to': end_date,
			})
			if today == date_utils.end_of(today, 'month'):
				self._create_monthly_report(employee, today)

	@api.model
	def _create_monthly_report(self, employee, date):
		start_date = date_utils.start_of(date, 'month')
		end_date = date_utils.end_of(date, 'month')
		weekly_records = self.search([
			('employee_id', '=', employee.id),
			('date_from', '>=', start_date),
			('date_to', '<=', end_date),
			('state', '=', 'done')
		])
		if not weekly_records:
			return
		monthly_data = {
			'employee_id': employee.id,
			'department_id': employee.department_id.id if employee.department_id else False,
			'date_from': start_date,
			'date_to': end_date,
		}
		monthly_record = self.create(monthly_data)
		monthly_record.message_post(body=f"Monthly performance report generated for {employee.name}.")

	@api.onchange('employee_id')
	def _onchange_employee_id(self):
		if self.employee_id and self.employee_id.department_id:
			self.department_id = self.employee_id.department_id
		else:
			self.department_id = False




class PerformanceAnalysisTimesheet(models.Model):
	_name = 'performance.analysis.timesheet'
	_description = 'Performance Analysis Timesheet Line'

	analysis_id = fields.Many2one('performance.analysis', string="Analysis")
	date = fields.Date(string="Date")
	name = fields.Char(string="Description")
	unit_amount = fields.Float(string="Hours")
	task_id = fields.Many2one('project.task', string="Task")
	project_id = fields.Many2one('project.project', string="Project")
	internal_hours = fields.Float(string="Internal Hours",tracking=True)


class ProjectTask(models.Model):
	_inherit = 'project.task'

	performance_analysis_id = fields.Many2one('performance.analysis', string='Performance Analysis', readonly=True) 
	

class PerformanceAnalysisTaskLine(models.Model):
	_name = 'performance.analysis.task.line'
	_description = 'Performance Analysis Task Line'


	performance_analysis_id = fields.Many2one('performance.analysis', string='Performance Analysis', readonly=True)
	analysis_id = fields.Many2one('performance.analysis', string="Analysis", ondelete='cascade',tracking=True)
	project_id = fields.Many2one('project.project', string="Project",tracking=True)
	task_id = fields.Many2one('project.task', string="Task",tracking=True)
	internal_hours = fields.Float(string="Internal Hours",tracking=True)
	total_internal_hours = fields.Float(string="Total Hours",tracking=True)
	stage_id = fields.Many2one('project.task.type', string='Stage',tracking=True, index=True,
		domain="[('project_ids', '=', project_id)]", copy=False)
	
	def _get_default_stage_id(self):
		project_id = self.env.context.get('default_project_id')
		if not project_id:
			return False
		return self.stage_find(project_id, [('fold', '=', False)])

	@api.model
	def _read_group_stage_ids(self, stages, domain, order):
		search_domain = [('id', 'in', stages.ids)]
		if 'default_project_id' in self.env.context:
			search_domain = ['|', ('project_ids', '=', self.env.context['default_project_id'])] + search_domain
		stage_ids = stages._search(search_domain, order=order, access_rights_uid=SUPERUSER_ID)
		return stages.browse(stage_ids)
		
	def action_view_task (self):
		self.ensure_one()
		return {
			'type': 'ir.actions.act_window',
			'res_model': 'project.task',
			'view_mode': 'form',
			'res_id': self.task_id.id,
			'target': 'current',
		}


class PerformanceLine(models.Model):
	_name = 'performance.line'
	_description = 'Performance Line'

	analysis_id = fields.Many2one('performance.analysis', string='Analysis', ondelete='cascade' ,tracking=True)
	start_date_new = fields.Date(string='Start Date',tracking=True)
	end_date_new = fields.Date(string='End Date',tracking=True)
	
	submit_timesheets = fields.Float(string='Submit Timesheets (0-5)', default=0.0,tracking=True)
	productivity = fields.Float(string='Productivity (0-5)', default=0.0,tracking=True)
	work_quality = fields.Float(string='Work Quality (0-5)', default=0.0,tracking=True)
	consistency = fields.Float(string='Consistency (0-5)', default=0.0)
	communication_skills = fields.Float(string='Communication Skills (0-5)', default=0.0,tracking=True)
	punctuality = fields.Float(string='Punctuality (0-5)', default=0.0,tracking=True)
	client_relations = fields.Float(string='Client Relations (0-5)', default=0.0,tracking=True)
	coworker_relations = fields.Float(string='Coworker Relations (0-5)', default=0.0,tracking=True)
	responsibility = fields.Float(string='Responsibility (0-5)', default=0.0,tracking=True)
	leadership_skills = fields.Float(string='Leadership Skills (0-5)', default=0.0,tracking=True)
	technical_skills = fields.Float(string='Technical Skills (0-5)', default=0.0,tracking=True)
	daily_meeting_participation = fields.Float(string='Daily Meeting Participation (0-5)', default=0.0,tracking=True)
	hr_policy_compliance = fields.Float(string='HR Policy Compliance (0-5)', default=0.0,tracking=True)
	manager_review = fields.Text(string='Manager Review',tracking=True)
	hr_review = fields.Text(string='HR Review',tracking=True)
	comments = fields.Text(string='Comments',tracking=True)
	weekly_feedback = fields.Text(string='Weekly Feedback', tracking=True)
	monthly_feedback = fields.Text(string='Monthly Feedback', tracking=True)
	performance_score = fields.Float(string='Performance Score', store=True,tracking=True)

	@api.constrains(
		'submit_timesheets', 'productivity', 'work_quality', 'consistency',
		'communication_skills', 'punctuality', 'client_relations',
		'coworker_relations', 'responsibility', 'leadership_skills',
		'technical_skills', 'daily_meeting_participation', 'hr_policy_compliance'
	)
	def _check_scores_range(self):
		for record in self:
			for field_name in [
				'submit_timesheets', 'productivity', 'work_quality', 'consistency',
				'communication_skills', 'punctuality', 'client_relations',
				'coworker_relations', 'responsibility', 'leadership_skills',
				'technical_skills', 'daily_meeting_participation', 'hr_policy_compliance'
			]:
				value = getattr(record, field_name)
				if value < 0 or value > 5:
					raise ValidationError(f"'{self._fields[field_name].string}' must be between 0 and 5.")

class PerformanceSummary(models.Model):
	_name = 'performance.summary'
	_description = 'Performance Summary'

	analysis_id = fields.Many2one('performance.analysis', string='Analysis', ondelete='cascade',tracking=True)
	week_number = fields.Char(string='Week Number',tracking=True)
	manager_review = fields.Text(string='Manager Review ', default=0.0,tracking=True)
	hr_review = fields.Text(string='HR Review', default=0.0,tracking=True)
	comments = fields.Text(string='Comments',tracking=True)
	performance_score_weekly = fields.Float(string='Performance Score Weekly (0-5)', store=True,tracking=True)


class PerformanceMonthly(models.Model):
	_name = 'performance.monthly'
	_description = 'Monthly Performance'

	analysis_id = fields.Many2one('performance.analysis', string='Analysis', ondelete='cascade',tracking=True)
	employee_name = fields.Char(string='Employee Name', compute='_compute_employee_name',tracking=True)
	manager_review = fields.Text(string='Manager Review', default=0.0,tracking=True)
	hr_review = fields.Text(string='HR Review', default=0.0,tracking=True)
	comments = fields.Text(string='Comments',tracking=True)
	performance_score_monthly = fields.Float(string='Performance Score Monthly(0-20)',tracking=True, store=True)

	@api.depends('analysis_id.employee_id')
	def _compute_employee_name(self):
		for record in self:
			record.employee_name = record.analysis_id.employee_id.name		