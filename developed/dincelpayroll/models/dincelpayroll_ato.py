from odoo import models, fields, api
from datetime import datetime, timedelta
import datetime as dt
import time
from dateutil import parser
import xml.etree.cElementTree as ET
from xml.etree import ElementTree
from xml.dom import minidom
from . import dincelpayroll_vars 
import logging
#import io

_logger = logging.getLogger(__name__)
# class openacademy(models.Model):
#     _name = 'openacademy.openacademy'

#     name = fields.Char()

class DincelPayrollATO(models.Model):
	_name = 'dincelpayroll.ato'
	_description = 'Payroll ATO'		
	def prettify(self, elem):
		"""Return a pretty-printed XML string for the Element.
		"""
		rough_string = ElementTree.tostring(elem, 'utf-8')
		reparsed = minidom.parseString(rough_string)
		return reparsed.toprettyxml(indent="  ")
		
	def xml_indent(self, elem, level=0):
		i = "\n" + level*"  "
		if len(elem):
			if not elem.text or not elem.text.strip():
				elem.text = i + "  "
			if not elem.tail or not elem.tail.strip():
				elem.tail = i
			for elem in elem:
				self.xml_indent(elem, level+1)
			if not elem.tail or not elem.tail.strip():
				elem.tail = i
		else:
			if level and (not elem.tail or not elem.tail.strip()):
				elem.tail = i	
	def create_payevent_xml_headerWorkingTest(self, payslips):	
		'''root = ET.Element("Record_Delimiter")
		root.set('DocumentID', '1.1')
		root.set('DocumentName', 'PAYEVNT')
		root.set('DocumentType', 'PARENT')
		root.set('RelatedDocumentID', '')'''
		
		#<tns:PAYEVNT xmlns:tns="http://www.sbr.gov.au/ato/payevnt" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:schemaLocation="http://www.sbr.gov.au/ato/payevnt #ato.payevnt.0003.2018.01.00.xsd">
		
		#tns = ET.SubElement(root, "tns:PAYEVNT")
		root = ET.Element("tns:PAYEVNT")
		root.set('xsi:schemaLocation', 'http://www.sbr.gov.au/ato/payevnt ato.payevnt.0003.2018.01.00.xsd')
		root.set('xmlns:xsi', 'http://www.w3.org/2001/XMLSchema-instance')
		root.set('xmlns:tns', 'http://www.sbr.gov.au/ato/payevnt')
		
		tns_rp = ET.SubElement(root, "tns:Rp")
		
		ET.SubElement(tns_rp, "tns:SoftwareInformationBusinessManagementSystemId").text	="2ec54020-d26c-11e8-b568-0800200c9a66"
		ET.SubElement(tns_rp, "tns:AustralianBusinessNumberId").text	="78083839614"
		ET.SubElement(tns_rp, "tns:OrganisationDetailsOrganisationBranchC").text= "1"
		
		org = ET.SubElement(tns_rp, "tns:OrganisationName")
		ET.SubElement(org, "tns:DetailsOrganisationalNameT").text = "DINCEL Construction System Pty Ltd"
		ET.SubElement(org, "tns:PersonUnstructuredNameFullNameT").text = "Semra Dokumcu"
		
		ect = ET.SubElement(tns_rp, "tns:ElectronicContact")
		ET.SubElement(ect, "tns:ElectronicMailAddressT").text	="payroll@dincel.com.au"
		ET.SubElement(ect, "tns:TelephoneMinimalN").text	="0296701633"
		
		post = ET.SubElement(tns_rp, "tns:AddressDetailsPostal")
		ET.SubElement(post, "tns:Line1T").text	="101 Quarry Road"
		ET.SubElement(post, "tns:LocalityNameT").text	="ERSKINE PARK"
		ET.SubElement(post, "tns:StateOrTerritoryC").text	="NSW"
		ET.SubElement(post, "tns:PostcodeT").text	="2759"
		ET.SubElement(post, "tns:CountryC").text	="au"
		
		pay = ET.SubElement(tns_rp, "tns:Payroll")
		ET.SubElement(pay, "tns:PaymentRecordTransactionD").text	="2020-01-20"
		ET.SubElement(pay, "tns:InteractionRecordCt").text	="%s" % (len(payslips))
		ET.SubElement(pay, "tns:MessageTimestampGenerationDt").text	="2020-01-20T13:30:00Z"
		ET.SubElement(pay, "tns:InteractionTransactionId").text	="BULK001"
		ET.SubElement(pay, "tns:AmendmentI").text	="false"
		tax = ET.SubElement(pay, "tns:IncomeTaxAndRemuneration")
		ET.SubElement(tax, "tns:PayAsYouGoWithholdingTaxWithheldA").text	="1823.00"
		ET.SubElement(tax, "tns:TotalGrossPaymentsWithholdingA").text	="1823.00"
		
		dec = ET.SubElement(tns_rp, "tns:Declaration")
		ET.SubElement(dec, "tns:SignatoryIdentifierT").text	="rajprasad"
		ET.SubElement(dec, "tns:SignatureD").text	="2020-01-20"
		ET.SubElement(dec, "tns:StatementAcceptedI").text	="true"
			 
			
		#self.xml_indent(root)
		#self.prettify(root)
		#@tree = ET.ElementTree(root)
		self.xml_indent(root)
		
		return root
		
		
	def create_payevent_xml_header(self, payslips, summary):	
		'''root = ET.Element("Record_Delimiter")
		root.set('DocumentID', '1.1')
		root.set('DocumentName', 'PAYEVNT')
		root.set('DocumentType', 'PARENT')
		root.set('RelatedDocumentID', '')'''
		
		#<tns:PAYEVNT xmlns:tns="http://www.sbr.gov.au/ato/payevnt" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:schemaLocation="http://www.sbr.gov.au/ato/payevnt #ato.payevnt.0003.2018.01.00.xsd">
		
		#tns = ET.SubElement(root, "tns:PAYEVNT")
		root = ET.Element("tns:PAYEVNT")
		root.set('xsi:schemaLocation', 'http://www.sbr.gov.au/ato/payevnt ato.payevnt.0003.2018.01.00.xsd')
		root.set('xmlns:xsi', 'http://www.w3.org/2001/XMLSchema-instance')
		root.set('xmlns:tns', 'http://www.sbr.gov.au/ato/payevnt')
		
		tns_rp = ET.SubElement(root, "tns:Rp")
		
		ET.SubElement(tns_rp, "tns:SoftwareInformationBusinessManagementSystemId").text	="2ec54020-d26c-11e8-b568-0800200c9a66"
		ET.SubElement(tns_rp, "tns:AustralianBusinessNumberId").text	="78083839614"
		ET.SubElement(tns_rp, "tns:OrganisationDetailsOrganisationBranchC").text= "1"
		
		org = ET.SubElement(tns_rp, "tns:OrganisationName")
		ET.SubElement(org, "tns:DetailsOrganisationalNameT").text = "DINCEL Construction System Pty Ltd"
		ET.SubElement(org, "tns:PersonUnstructuredNameFullNameT").text = "Semra Dokumcu"
		
		ect = ET.SubElement(tns_rp, "tns:ElectronicContact")
		ET.SubElement(ect, "tns:ElectronicMailAddressT").text	="payroll@dincel.com.au"
		ET.SubElement(ect, "tns:TelephoneMinimalN").text	="0296701633"
		
		post = ET.SubElement(tns_rp, "tns:AddressDetailsPostal")
		ET.SubElement(post, "tns:Line1T").text	="101 Quarry Road"
		ET.SubElement(post, "tns:LocalityNameT").text	="ERSKINE PARK"
		ET.SubElement(post, "tns:StateOrTerritoryC").text	="NSW"
		ET.SubElement(post, "tns:PostcodeT").text	="2759"
		ET.SubElement(post, "tns:CountryC").text	="au"
		
		pay = ET.SubElement(tns_rp, "tns:Payroll")
		ET.SubElement(pay, "tns:PaymentRecordTransactionD").text	="%s" % (summary['pay_date'])#"2020-01-20"
		ET.SubElement(pay, "tns:InteractionRecordCt").text	="%s" % (len(payslips))
		ET.SubElement(pay, "tns:MessageTimestampGenerationDt").text	="%s" % (summary['message_time'])#"2020-01-20T13:30:00Z"
		ET.SubElement(pay, "tns:InteractionTransactionId").text	="BULK001"
		ET.SubElement(pay, "tns:AmendmentI").text	="false"
		tax = ET.SubElement(pay, "tns:IncomeTaxAndRemuneration")
		ET.SubElement(tax, "tns:PayAsYouGoWithholdingTaxWithheldA").text	="%s" % (summary['payg_tax'])
		ET.SubElement(tax, "tns:TotalGrossPaymentsWithholdingA").text	="%s" % (summary['tax_gross'])
		
		dec = ET.SubElement(tns_rp, "tns:Declaration")
		ET.SubElement(dec, "tns:SignatoryIdentifierT").text	="rajprasad"
		ET.SubElement(dec, "tns:SignatureD").text	="2020-01-20"
		ET.SubElement(dec, "tns:StatementAcceptedI").text	="true"
			 
			
		#self.xml_indent(root)
		#self.prettify(root)
		#@tree = ET.ElementTree(root)
		self.xml_indent(root)
		return root
		
	def create_payevent_xml_body_workingTest(self, payslips):
		#-------------------------------------
		'''record = ET.Element("Record_Delimiter")
		record.set('DocumentID', '1.2')
		record.set('DocumentName', 'PAYEVNT')
		record.set('DocumentType', 'CHILD')
		record.set('RelatedDocumentID', '1.1')'''
		
		#paytmp = ET.SubElement(record, "tns:PAYEVNTEMP")
		record = ET.Element("tns:PAYEVNTEMP")
		record.set('xmlns:tns', 'http://www.sbr.gov.au/ato/payevntemp')
		record.set('xmlns:xsi', 'http://www.w3.org/2001/XMLSchema-instance')
		record.set('xsi:schemaLocation', 'http://www.sbr.gov.au/ato/payevntemp ato.payevntemp.0003.2018.01.00.xsd') 
		#paytmp=record
		payee = ET.SubElement(record, "tns:Payee")
		
		idntf = ET.SubElement(payee, "tns:Identifiers")
		ET.SubElement(idntf, "tns:TaxFileNumberId").text="857055954"
		ET.SubElement(idntf, "tns:EmploymentPayrollNumberId").text="10092"
		
		perdet = ET.SubElement(payee, "tns:PersonNameDetails")
		ET.SubElement(perdet, "tns:FamilyNameT").text="Rai"
		ET.SubElement(perdet, "tns:GivenNameT").text="Shukra"
		
		perdem = ET.SubElement(payee, "tns:PersonDemographicDetails")
		ET.SubElement(perdem, "tns:BirthDm").text="10"
		ET.SubElement(perdem, "tns:BirthM").text="06"
		ET.SubElement(perdem, "tns:BirthY").text="1980"
		
		peradr = ET.SubElement(payee, "tns:AddressDetails")
		ET.SubElement(peradr, "tns:Line1T").text="11 Steenson St"
		ET.SubElement(peradr, "tns:LocalityNameT").text="Edmondson Park"
		ET.SubElement(peradr, "tns:StateOrTerritoryC").text="NSW"
		ET.SubElement(peradr, "tns:PostcodeT").text="2174"
		ET.SubElement(peradr, "tns:CountryC").text="au"
		
		ecc = ET.SubElement(payee, "tns:ElectronicContact")
		ET.SubElement(ecc, "tns:ElectronicMailAddressT").text="shukrarai@hotmail.com"
		cdn = ET.SubElement(payee, "tns:EmployerConditions") 
		
		etax = ET.SubElement(payee, "tns:RemunerationIncomeTaxPayAsYouGoWithholding")
		period = ET.SubElement(etax, "tns:PayrollPeriod")
		ET.SubElement(period, "tns:StartD").text="2019-12-30"
		ET.SubElement(period, "tns:EndD").text="2020-01-12"
		ET.SubElement(period, "tns:PayrollEventFinalI").text="false"
		
		inonb = ET.SubElement(etax, "tns:IndividualNonBusiness")
		ET.SubElement(inonb, "tns:GrossA").text="32654"
		ET.SubElement(inonb, "tns:TaxWithheldA").text="1823"
		
		allow = ET.SubElement(etax, "tns:AllowanceCollection")
		allow1 = ET.SubElement(allow, "tns:Allowance")
		ET.SubElement(allow1, "tns:TypeC").text="Car"
		ET.SubElement(allow1, "tns:IndividualNonBusinessEmploymentAllowancesA").text="50.52"
		
		dedc = ET.SubElement(etax, "tns:DeductionCollection")
		dedc1 = ET.SubElement(dedc, "tns:Deduction")
		ET.SubElement(dedc1, "tns:TypeC").text="Fees"
		ET.SubElement(dedc1, "tns:A").text="25.50"
		super = ET.SubElement(etax, "tns:SuperannuationContribution")
		ET.SubElement(super, "tns:EmployerContributionsSuperannuationGuaranteeA").text="980.32"
		
		fringe = ET.SubElement(etax, "tns:IncomeFringeBenefitsReportable")
		
		self.xml_indent(record)
		#self.prettify(root)
		#tree = ET.ElementTree(record)
		return record
	def create_payevent_xml_body(self,api_publish,  payslip):
		#-------------------------------------
		'''record = ET.Element("Record_Delimiter")
		record.set('DocumentID', '1.2')
		record.set('DocumentName', 'PAYEVNT')
		record.set('DocumentType', 'CHILD')
		record.set('RelatedDocumentID', '1.1')'''
		
		#paytmp = ET.SubElement(record, "tns:PAYEVNTEMP")
		record = ET.Element("tns:PAYEVNTEMP")
		record.set('xmlns:tns', 'http://www.sbr.gov.au/ato/payevntemp')
		record.set('xmlns:xsi', 'http://www.w3.org/2001/XMLSchema-instance')
		record.set('xsi:schemaLocation', 'http://www.sbr.gov.au/ato/payevntemp ato.payevntemp.0003.2018.01.00.xsd') 
		#paytmp=record
		payee = ET.SubElement(record, "tns:Payee")
		
		idntf = ET.SubElement(payee, "tns:Identifiers")
		#if api_publish=="test":
		#	tfn="123456789"
		#else:
		#	tfn=payslip.employee_id.x_tfn.replace(" ","") or ""
		tfn=payslip.employee_id.x_tfn.replace(" ","") or ""
		ET.SubElement(idntf, "tns:TaxFileNumberId").text="%s" % (tfn)
		ET.SubElement(idntf, "tns:EmploymentPayrollNumberId").text="%s"  % (payslip.number)
		
		perdet = ET.SubElement(payee, "tns:PersonNameDetails")
		ET.SubElement(perdet, "tns:FamilyNameT").text="%s"  % (payslip.x_last_name)
		ET.SubElement(perdet, "tns:GivenNameT").text="%s"  % (payslip.x_first_name)
		
		dt=parser.parse(str(payslip.employee_id.birthday)) #dt.day, dt2.day, dt2.month, dt2.year
		perdem = ET.SubElement(payee, "tns:PersonDemographicDetails")
		ET.SubElement(perdem, "tns:BirthDm").text="%s"  % (dt.day)
		ET.SubElement(perdem, "tns:BirthM").text="%s"  % (dt.month)
		ET.SubElement(perdem, "tns:BirthY").text="%s"  % (dt.year)
		
		peradr = ET.SubElement(payee, "tns:AddressDetails")
		ET.SubElement(peradr, "tns:Line1T").text="%s" % (payslip.employee_id.x_street)
		ET.SubElement(peradr, "tns:LocalityNameT").text="%s" % (payslip.employee_id.x_suburb)
		ET.SubElement(peradr, "tns:StateOrTerritoryC").text="%s" % ((payslip.employee_id.x_state_id and payslip.employee_id.x_state_id.code) or "NSW")
		ET.SubElement(peradr, "tns:PostcodeT").text="%s" % (payslip.employee_id.x_postcode)
		ET.SubElement(peradr, "tns:CountryC").text="au"
		
		if payslip.employee_id.x_email:
			ecc = ET.SubElement(payee, "tns:ElectronicContact")
			ET.SubElement(ecc, "tns:ElectronicMailAddressT").text="%s" % (payslip.employee_id.x_email)
			cdn = ET.SubElement(payee, "tns:EmployerConditions") 
		
		etax = ET.SubElement(payee, "tns:RemunerationIncomeTaxPayAsYouGoWithholding")
		period = ET.SubElement(etax, "tns:PayrollPeriod")
		ET.SubElement(period, "tns:StartD").text="%s" % (payslip.date_from)
		ET.SubElement(period, "tns:EndD").text="%s" % (payslip.date_to)
		ET.SubElement(period, "tns:PayrollEventFinalI").text="false"
		
		#gross_amt=payslip.x_gross_payslip_amt or 0.0	#except salary sacrifice-----------
		gross_amt=payslip.x_gross_amt or 0.0
		gross_amt=abs(round(float(gross_amt),2))
		tax_amt=payslip.x_tax_amt or 0.0
		tax_amt=abs(round(float(tax_amt),2))
		
		inonb = ET.SubElement(etax, "tns:IndividualNonBusiness")
		ET.SubElement(inonb, "tns:GrossA").text="%s" % (gross_amt)
		ET.SubElement(inonb, "tns:TaxWithheldA").text="%s" % (tax_amt)
		
		for line in payslip.x_summary_ids:
			amt=line.sub_total or 0.0
			amt=abs(round(float(amt),2))
			if line.category_id.category=="allowance":
				allow = ET.SubElement(etax, "tns:AllowanceCollection")
				allow1 = ET.SubElement(allow, "tns:Allowance")
				ET.SubElement(allow1, "tns:TypeC").text="%s" % (line.category_id.allowance_type.title())
				ET.SubElement(allow1, "tns:IndividualNonBusinessEmploymentAllowancesA").text="%s" % (amt)
			elif line.category_id.category=="deduction":
				dedc = ET.SubElement(etax, "tns:DeductionCollection")
				dedc1 = ET.SubElement(dedc, "tns:Deduction")
				#dict(self._fields['dayofweek'].selection).get(self.dayofweek) deduction_type
				 
				#deduct_type=dincelpayroll_vars.DEDUCTION_OPTIONS[str(line.category_id.deduction_type)]
				deduct_type=line.category_id.deduction_type.title()
				#_logger.error("PAY_CATEGORY_OPTIONS[%s]deduction_type [%s] category_id[%s]" % (deduct_type, line.category_id.deduction_type,line.category_id.id))
				ET.SubElement(dedc1, "tns:TypeC").text="%s" % (deduct_type) #(line.category_id.deduction_type.title())#deduction_type#"Fees"
				ET.SubElement(dedc1, "tns:A").text="%s" % (amt)
		super = ET.SubElement(etax, "tns:SuperannuationContribution")
		ET.SubElement(super, "tns:EmployerContributionsSuperannuationGuaranteeA").text="%s" % (payslip.x_super_amt)
		
		fringe = ET.SubElement(etax, "tns:IncomeFringeBenefitsReportable")
		
		self.xml_indent(record)
		#self.prettify(root)
		#tree = ET.ElementTree(record)
		return record	
		
		
	def create_payevent_xml(self, payslips):
		#//_path  	= "/var/tmp/odoo/payslips/"
		_path		= self.env['dincelaccount.settings'].get_odoo_tmp_folder() + "/payslips/"
		api_publish	= self.env['dincelaccount.settings'].get_api_publish()
		#-------------------------------------
		#pay_date= str(datetime.today() - timedelta(days=1))[:10]
		yesterday = datetime.today() - timedelta(days=1)
		pay_date=str(yesterday)[:10]
		
		#FORMAT='%Y-%m-%dT%H:%M:%S%z'
		##"2020-01-20T13:30:00Z"
		#message_time1=datetime.strptime(time.strftime(FORMAT, time.localtime()),FORMAT)
		#:00Z
		FORMAT='%Y-%m-%d %H:%M:00'
		message_time=datetime.strptime(time.strftime(FORMAT, time.localtime()),FORMAT)
		message_time=str(message_time).replace(" ","T")+"Z"
		#_logger.error("create_payevent_xml message_time1[%s] message_time[%s]" % (message_time, message_time))
		payg_tax="200"
		tax_gross="2000"
		
		summary={'pay_date':pay_date,'message_time':message_time,'payg_tax':payg_tax,'tax_gross':tax_gross}
		
		icount=1
		root 	= self.create_payevent_xml_header(payslips, summary)
		#tree 	= ET.ElementTree(root)
		xml_str ='<Record_Delimiter DocumentID="1.1" DocumentType="PARENT" DocumentName="PAYEVNT" RelatedDocumentID=""/>'
		xml_str += ElementTree.tostring(root, encoding='unicode')

		
		for payslip in payslips:
			#tree2 	= ET.ElementTree(record)
			#tree = tree.getroot()
			icount+=1
			#tree2  = tree.getroot()
			xml_str +='<Record_Delimiter DocumentID="1.%s" DocumentType="CHILD" DocumentName="PAYEVNTEMP" RelatedDocumentID="1.1"/>' % (icount)
			
			record 	= self.create_payevent_xml_body(api_publish, payslip)
			xml_str += ElementTree.tostring(record, encoding='unicode')
			
			
		#_logger.error("create_payevent_xmlcreate_payevent_xml[%s]" % (xml_str))
		#parser 	= ET.XMLParser(recover=True)
		#tree_new 	= ET.ElementTree(ET.fromstring(xml_str, parser=parser)) 
		#tree_new 	= ET.parse(xml_str)
		#tree_new 	= ET.ElementTree(ET.fromstring(xml_str))
		#f 			= io.StringIO(str(xml_str))
		#tree_new 	= ET.parse(f)
		dttime1		= str(datetime.today())[:10]
		dttime2		= dttime1.replace("-", "")
		code="PAYEVNT-SUBMIT"
		sequence=self.env['dincelpayroll.sequence'].get_next_number_bydate(code)#.zfill(3)
		sequence = str(sequence).zfill(3)
		fname = "%s-%s-%s.txt" % (code, dttime2, sequence)
		#fname= "PAYEVNT-SUBMIT-%s-001.txt" % (dttime2)
		#tree_new.write(_path + fname)
		model, idid, title="dincelpayroll.ato", self.id, "ATO STP File"
		self.env['dincel.utils'].write_file(_path, fname,  xml_str)
		'''#return {
			'name': 'Aba File',
			'res_model': 'ir.actions.act_url',
			'type' : 'ir.actions.act_url',
			'url': '/web/binary/download_file?model=dincelaccount.aba&field=datas&id=%s&path=%s&filename=%s' % (self.id,_path,fname),
			'context': {}}	'''
		#return self.env['dincel.utils'].download_file(model, idid, title, _path, fname)
		#return True
		return self.env['dincel.utils'].download_file(model, idid, title, _path, fname)
		
	def create_payevent_xmlTest(self, payslips):
		#//_path  	= "/var/tmp/odoo/payslips/"
		_path	=self.env['dincelaccount.settings'].get_odoo_tmp_folder() + "/payslips/"
		
		root = ET.Element("Record_Delimiter")
		root.set('DocumentID', '1.1')
		root.set('DocumentName', 'PAYEVNT')
		root.set('DocumentType', 'PARENT')
		root.set('RelatedDocumentID', '')
		
		#<tns:PAYEVNT xmlns:tns="http://www.sbr.gov.au/ato/payevnt" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:schemaLocation="http://www.sbr.gov.au/ato/payevnt #ato.payevnt.0003.2018.01.00.xsd">
		
		tns = ET.SubElement(root, "tns:PAYEVNT")
		tns.set('xmlns:tns', 'http://www.sbr.gov.au/ato/payevnt')
		tns.set('xmlns:xsi', 'http://www.w3.org/2001/XMLSchema-instance"')
		tns.set('xsi:schemaLocation', 'http://www.sbr.gov.au/ato/payevnt ato.payevnt.0003.2018.01.00.xsd')
		tns_rp = ET.SubElement(tns, "tns:Rp")
		
		ET.SubElement(tns_rp, "tns:SoftwareInformationBusinessManagementSystemId").text	="2ec54020-d26c-11e8-b568-0800200c9a66"
		ET.SubElement(tns_rp, "tns:AustralianBusinessNumberId").text	="78083839614"
		ET.SubElement(tns_rp, "tns:OrganisationDetailsOrganisationBranchC").text= "1"
		
		org = ET.SubElement(tns_rp, "tns:OrganisationName")
		ET.SubElement(org, "tns:DetailsOrganisationalNameT").text = "DINCEL Construction System Pty Ltd"
		ET.SubElement(org, "tns:PersonUnstructuredNameFullNameT").text = "Semra Dokumcu"
		
		ect = ET.SubElement(tns_rp, "tns:ElectronicContact")
		ET.SubElement(ect, "tns:ElectronicMailAddressT").text	="payroll@dincel.com.au"
		ET.SubElement(ect, "tns:TelephoneMinimalN").text	="0296701633"
		
		post = ET.SubElement(tns_rp, "tns:AddressDetailsPostal")
		ET.SubElement(post, "tns:Line1T").text	="101 Quarry Road"
		ET.SubElement(post, "tns:LocalityNameT").text	="ERSKINE PARK"
		ET.SubElement(post, "tns:StateOrTerritoryC").text	="NSW"
		ET.SubElement(post, "tns:PostcodeT").text	="2759"
		ET.SubElement(post, "tns:CountryC").text	="au"
		
		pay = ET.SubElement(tns_rp, "tns:Payroll")
		ET.SubElement(pay, "tns:PaymentRecordTransactionD").text	="2020-01-20"
		ET.SubElement(pay, "tns:InteractionRecordCt").text	="1"
		ET.SubElement(pay, "tns:MessageTimestampGenerationDt").text	="2020-01-20T13:30:00Z"
		ET.SubElement(pay, "tns:InteractionTransactionId").text	="BULK001"
		ET.SubElement(pay, "tns:AmendmentI").text	="false"
		tax = ET.SubElement(pay, "tns:IncomeTaxAndRemuneration")
		ET.SubElement(tax, "tns:PayAsYouGoWithholdingTaxWithheldA").text	="1823.00"
		ET.SubElement(tax, "tns:TotalGrossPaymentsWithholdingA").text	="1823.00"
		
		dec = ET.SubElement(tns_rp, "tns:Declaration")
		ET.SubElement(dec, "tns:SignatoryIdentifierT").text	="rajprasad"
		ET.SubElement(dec, "tns:SignatureD").text	="2020-01-20"
		ET.SubElement(dec, "tns:StatementAcceptedI").text	="true"
			 
			
		self.xml_indent(root)
		#self.prettify(root)
		tree = ET.ElementTree(root)
		
		#-------------------------------------
		###
		record = ET.Element("Record_Delimiter")
		record.set('DocumentID', '1.2')
		record.set('DocumentName', 'PAYEVNT')
		record.set('DocumentType', 'CHILD')
		record.set('RelatedDocumentID', '1.1')
		
		paytmp = ET.SubElement(record, "tns:PAYEVNTEMP")
		paytmp.set('xmlns:tns', 'http://www.sbr.gov.au/ato/payevntemp')
		paytmp.set('xmlns:xsi', 'http://www.w3.org/2001/XMLSchema-instance"')
		paytmp.set('xsi:schemaLocation', 'http://www.sbr.gov.au/ato/payevntemp ato.payevntemp.0003.2018.01.00.xsd') 
		
		payee = ET.SubElement(paytmp, "tns:Payee")
		idntf = ET.SubElement(payee, "tns:Identifiers")
		ET.SubElement(idntf, "tns:TaxFileNumberId").text="857055954"
		ET.SubElement(idntf, "tns:EmploymentPayrollNumberId").text="10092"
		
		perdet = ET.SubElement(payee, "tns:PersonNameDetails")
		ET.SubElement(perdet, "tns:FamilyNameT").text="Rai"
		ET.SubElement(perdet, "tns:GivenNameT").text="Shukra"
		
		perdem = ET.SubElement(payee, "tns:PersonDemographicDetails")
		ET.SubElement(perdem, "tns:BirthDm").text="10"
		ET.SubElement(perdem, "tns:BirthM").text="06"
		ET.SubElement(perdem, "tns:BirthY").text="1980"
		
		peradr = ET.SubElement(payee, "tns:AddressDetails")
		ET.SubElement(peradr, "tns:Line1T").text="11 Steenson St"
		ET.SubElement(peradr, "tns:LocalityNameT").text="Edmondson Park"
		ET.SubElement(peradr, "tns:StateOrTerritoryC").text="NSW"
		ET.SubElement(peradr, "tns:PostcodeT").text="2174"
		ET.SubElement(peradr, "tns:CountryC").text="au"
		
		ecc = ET.SubElement(payee, "tns:ElectronicContact")
		ET.SubElement(ecc, "tns:ElectronicMailAddressT").text="shukrarai@hotmail.com"
		cdn = ET.SubElement(payee, "tns:EmployerConditions") 
		
		etax = ET.SubElement(payee, "tns:RemunerationIncomeTaxPayAsYouGoWithholding")
		period = ET.SubElement(etax, "tns:PayrollPeriod")
		ET.SubElement(period, "tns:StartD").text="2019-12-30"
		ET.SubElement(period, "tns:EndD").text="2020-01-12"
		ET.SubElement(period, "tns:PayrollEventFinalI").text="false"
		
		inonb = ET.SubElement(etax, "tns:IndividualNonBusiness")
		ET.SubElement(inonb, "tns:GrossA").text="32654"
		ET.SubElement(inonb, "tns:TaxWithheldA").text="1823"
		
		allow = ET.SubElement(etax, "tns:AllowanceCollection")
		allow1 = ET.SubElement(allow, "tns:Allowance")
		ET.SubElement(allow1, "tns:TypeC").text="Car"
		ET.SubElement(allow1, "tns:IndividualNonBusinessEmploymentAllowancesA").text="50.52"
		
		dedc = ET.SubElement(etax, "tns:DeductionCollection")
		dedc1 = ET.SubElement(dedc, "tns:Deduction")
		ET.SubElement(dedc1, "tns:TypeC").text="Fees"
		ET.SubElement(dedc1, "tns:A").text="25.50"
		super = ET.SubElement(etax, "tns:SuperannuationContribution")
		ET.SubElement(super, "tns:EmployerContributionsSuperannuationGuaranteeA").text="980.32"
		
		fringe = ET.SubElement(etax, "tns:IncomeFringeBenefitsReportable")
		
		self.xml_indent(record)
		#self.prettify(root)
		tree = ET.ElementTree(record)
		tree.write(_path + "PAYEVNT.xml")
		
		