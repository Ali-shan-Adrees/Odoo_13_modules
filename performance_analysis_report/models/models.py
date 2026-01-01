from odoo import models
import xlsxwriter

class PerformanceAnalysisReport(models.AbstractModel):
	_name = 'report.performance_analysis.performance_analysis_xlsx'
	_inherit = 'report.report_xlsx.abstract'

	def generate_xlsx_report(self, workbook, data, records):
		# Create a worksheet
		sheet = workbook.add_worksheet('Performance Analysis')

		# Define formats
		bold = workbook.add_format({'bold': True, 'bg_color': '#D3D3D3'})
		title = workbook.add_format({'bold': True, 'font_size': 14, 'align': 'center'})
		header = workbook.add_format({'bold': True, 'bg_color': '#E6E6FA', 'border': 1})

		# Write report title
		sheet.merge_range('A1:E1', 'Performance Analysis Report', title)
		sheet.set_column('A:E', 20)

		# Write headers for Employee Details
		sheet.write('A3', 'Employee Details', bold)
		sheet.write('A4', 'Employee Name', header)
		sheet.write('B4', 'Department', header)
		sheet.write('C4', 'From Date', header)
		sheet.write('D4', 'To Date', header)

		# Write Employee Details
		row = 4
		for record in records:
			row += 1
			sheet.write(row, 0, record.employee_id.name or '')
			sheet.write(row, 1, record.department_id.name or '')
			sheet.write(row, 2, str(record.date_from) or '')
			sheet.write(row, 3, str(record.date_to) or '')

		# Write headers for Weekly Summary
		sheet.write('A7', 'Weekly Summary', bold)
		sheet.write('A8', 'Week Number', header)
		sheet.write('B8', 'Manager Review', header)
		sheet.write('C8', 'HR Review', header)
		sheet.write('D8', 'Comments', header)
		sheet.write('E8', 'Performance Score Weekly', header)

		# Write Weekly Summary
		row = 8
		for record in records:
			for summary in record.weekly_summary:
				row += 1
				sheet.write(row, 0, summary.week_number or '')
				sheet.write(row, 1, summary.manager_review or 0.0)
				sheet.write(row, 2, summary.hr_review or 0.0)
				sheet.write(row, 3, summary.comments or '')
				sheet.write(row, 4, summary.performance_score_weekly or 0.0)

		# Write headers for Monthly Progress
		sheet.write('A' + str(row + 2), 'Monthly Progress', bold)
		sheet.write('A' + str(row + 3), 'Employee Name', header)
		sheet.write('B' + str(row + 3), 'Manager Review', header)
		sheet.write('C' + str(row + 3), 'HR Review', header)
		sheet.write('D' + str(row + 3), 'Comments', header)
		sheet.write('E' + str(row + 3), 'Performance Score Monthly', header)

		# Write Monthly Progress
		row = row + 3
		for record in records:
			for monthly in record.monthly_performance:
				row += 1
				sheet.write(row, 0, monthly.employee_name or '')
				sheet.write(row, 1, monthly.manager_review or 0.0)
				sheet.write(row, 2, monthly.hr_review or 0.0)
				sheet.write(row, 3, monthly.comments or '')
				sheet.write(row, 4, monthly.performance_score_monthly or 0.0)

	def get_report_filename(self, options):
		record = self.env['performance.analysis'].browse(self.env.context.get('active_id'))
		employee_name = record.employee_id.name or "Employee"
		date_from = record.date_from or ""
		date_to = record.date_to or ""
		
		filename = f"{employee_name}_{date_from}_to_{date_to}.xlsx".strip('_')  # Remove leading/trailing underscores if dates are empty
		return filename or 'Performance_Analysis_Report.xlsx'  # Ensure non-empty		