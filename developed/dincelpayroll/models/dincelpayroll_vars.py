PAY_CATEGORY_OPTIONS=[
		('allowance', 'Allowance'),
		('deduction', 'Deduction'),
		('entitle', 'Entitlements'),
		('etp', 'ETP'),
		('foreign', 'Foreign Income'),
		('hire', 'Labour Hire'),
		('leave', 'Leaves'),
		('lumpsum', 'Lump Sum Payment'),
		('super', 'Super'),
		('tax', 'TAX'),
		('voluntary', 'Voluntary Payment'),
		('wage', 'Wage'),
		('workholiday', 'Work Holiday'),
		('zone', 'Zoning/JPDA'),
		]
		
YTD_CATEGORY_OPTIONS=[
			('gross', 'Gross Taxable'),
			('tax', 'Tax'),
			('net', 'Net'),
			('super', 'Super'),
			('personal', 'Personal Leave'),
			('annual', 'Annual Leave'),
			('longservice', 'Long Service Leave'),
			('item', 'Pay Category/Item'),
			]			
			
PAY_FREQUENCY_OPTIONS=[
			('week', 'Weekly'),
			('fortnight', 'Fortnightly'),
			('month', 'Monthly'),
			]
			
HR_UOM_OPTIONS=[
			('day', 'Days'),
			('week', 'Weeks'),
			]	#dincelpayroll_vars.HR_UOM_OPTIONS
			
# https://docs.python.org/2/library/datetime.html#date.weekday()			
WEEK_DAY_OPTIONS=[
			('0', 'Mon'),
			('1', 'Tue'),
			('2', 'Wed'),
			('3', 'Thu'),
			('4', 'Fri'),
			('5', 'Sat'),
			('6', 'Sun'),		
			]		
			
WEEK_DAY_OPTIONS_ARR=["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]	

TAX_SCALE_OPTIONS=[
			('1', 'Scale 1'),
			('2', 'Scale 2'),
			('3', 'Scale 3'),
			('4', 'Scale 4'),
			('5', 'Scale 5'),
			('6', 'Scale 6')
			]						
			
PAY_TYPE_OPTIONS=[
			('na', 'NA'),
			('base', 'Normal Pay'),
			('ot15', 'OT1.5'),
			('ot20', 'OT2.0'),
			('ot25', 'OT2.5'),
			('loading_leave', 'Loading Annual Leave'),
			('loading_night', 'Loading Night Shift'),
			('loading_noon', 'Loading Afternoon Shift'),
			('paid_break', 'Paid Break'),
			('leave_annual', 'Leave - Annual'),
			('leave_personal', 'Leave - Personal'),
			('leave_partday', 'Leave - Part Day'),		
			]			
			
LEAVE_TYPE_OPTIONS=[
			('annual', 'Annual Leave'),
			('nopay', 'No Pay'),
			('breavement', 'Breavement Leave'),
			('community', 'Community Leave'),
			('compensation', 'Compensation Leave'),
			('longservice', 'Long Service Leave'),
			('parental', 'Parental Leave'),
			('personal', 'Personal Leave'),
			('partday', 'Part Day Leave'),
			('public', 'Public Holiday'),
			]	
			
PAYSLIP_DELIVERY_OPTIONS=[
			('email', 'Email'),
			('print', 'Print'),
			('emailprint', 'Email and print'),
			('already', 'Already emailed printed'),
			]		
			
PAYSLIP_CREATE_OPTIONS=[
			('autopay', 'Autopay / Salary'),
			('manual', 'Manual / Casual Pay'),
			('timesheet', 'Timesheet Pay'),
			('import', 'Timesheet Import'),
			('terminate', 'Termination Pay'),
			#('suspend', 'Suspend Pay'),
			]				
 
			
IMPORT_COPY_STATE_OPTIONS=[
			('draft', 'Draft'),
			('confirm', 'Approved'),
			('done', 'Done'),
			]
			
ALLOWANCE_OPTIONS=[
			('car', 'Car'),
			('transport', 'Transport'),
			('laundry', 'Laundry'),
			('meals', 'Meals'),
			('travel', 'Travel'),
			('other', 'Other'),
			]						

SUPER_TYPE_OPTIONS=[
			('super', 'Super Guarantee'),
			('personal', 'Personal'),
			('sacrifice', 'Salary Sacrifice'),
			('employer', 'Employer Additional'),
			('spouse', 'Spouce'),
			('award', 'Award / Productivity'),
			]	
			
DEDUCTION_OPTIONS=[
			('fees', 'Fees'),
			('workplacegiving', 'Workplace Giving'),
			]	
SPECIALPAY_OPTIONS=[
			('auto', 'Auto Pay'),
			('loading', 'Loading Pay'),
			]	
			
PAYSLIP_MANAGE_OPTIONS=[
			('print', 'Print'),
			('email', 'Email'),
			('aba', 'Aba Generate'),
			('payevent', 'ATO PayEvent'),
			]		
			
WORK_TYPE_OPTIONS=[
			('work', 'Must work'),
			('optional', 'Work Optional'),
			('off', 'Day off'),
			]	
			
TS_FACTOR_TYPE_OPTIONS=[
			('rate', 'Rate'),
			('hrs', 'Hours'),
			]	
			
TS_INOUT_OPTIONS=[
			('IN', 'IN'),
			('OUT', 'OUT'),
			]	
			
TS_IMPORT_TYPE_OPTIONS=[
			('peoplekey', 'PeopleKey'),
			('myob', 'MYOB - Peoplekey'),
			('ascii', 'ASCII - Peoplekey'),
			]	
			
PAYSLIP_APP_OPTIONS=[
			('peoplekey', 'PeopleKey'),
			]										
			
HOUR_TYPE_OPTIONS=[
			('fixed', 'Fixed'),
			('balance', 'Balance'),
			('bal2max', 'Balance with Max'),
			]
			
API_PUBLISH_OPTIONS=[
			('test', 'Test'),
			('production', 'Production'),
			]						