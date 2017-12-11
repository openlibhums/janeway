__copyright__ = "Copyright 2017 Birkbeck, University of London"
__author__ = "Martin Paul Eve & Andy Byers"
__license__ = "AGPL v3"
__maintainer__ = "Birkbeck Centre for Technology and Publishing"

from dateutil.rrule import rrule, MONTHLY
from dateutil.relativedelta import relativedelta

import csv
import json

from django.http import HttpResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt

import press.models
from django.utils import timezone

from metrics import logic

from bs4 import BeautifulSoup


@csrf_exempt
def sushi(request):
    # a hacky SOAP implementation
    # test this using pycounter (from pip)
    # report = pycounter.sushi.get_report(wsdl_url='http://localhost:8000/metrics/sushi/',
    # start_date=datetime.date(2015,1,1), end_date=datetime.date(2017,1,31), requestor_id="myreqid",
    # customer_reference="refnum", report="JR1", release=4)

    # input looks like this:
    # b'<?xml version=\'1.0\' encoding=\'utf-8\'?>\n
    # <SOAP-ENV:Envelope xmlns:counter="http://www.niso.org/schemas/counter"
    # xmlns:sushicounter="http://www.niso.org/schemas/sushi/counter" xmlns:sushi="http://www.niso.org/schemas/sushi"
    # xmlns:SOAP-ENV="http://schemas.xmlsoap.org/soap/envelope/">\n  <SOAP-ENV:Body>\n
    # <sushicounter:ReportRequest Created="2017-01-21T18:45:38.463223+00:00" ID="e102313a-96b4-4bc6-81c4-529aa9a5dffc">
    # \n      <sushi:Requestor>\n        <sushi:ID>myreqid</sushi:ID>\n        <sushi:Name/>\n        <sushi:Email/>\n
    #      </sushi:Requestor>\n      <sushi:CustomerReference>\n        <sushi:ID>refnum</sushi:ID>\n
    #    <sushi:Name/>\n      </sushi:CustomerReference>\n      <sushi:ReportDefinition Name="JR1" Release="4">\n
    #      <sushi:Filters>\n          <sushi:UsageDateRange>\n            <sushi:Begin>2015-01-01</sushi:Begin>\n
    #        <sushi:End>2017-01-31</sushi:End>\n          </sushi:UsageDateRange>\n        </sushi:Filters>\n
    #    </sushi:ReportDefinition>\n    </sushicounter:ReportRequest>\n  </SOAP-ENV:Body>\n</SOAP-ENV:Envelope>\n'
    body = BeautifulSoup(request.body, 'xml')

    # TODO: pass through parameters like the requestor ID etc. and echo them back in the XML
    try:
        report_type = body.find('ReportDefinition').attrs['Name']
        report_request_id = body.find('ReportRequest').attrs['ID']

        requestor = body.find('Requestor')
        requestor_id = requestor.find('ID').text
        requestor_email = requestor.find('Email').text
        requestor_name = requestor.find('Name').text

        customer = body.find('CustomerReference')
        customer_ID = customer.find('ID').text
        customer_name = customer.find('Name').text
    except AttributeError:
        return HttpResponse(json.dumps({'Error': 'Malformed request.'}))

    if report_type.upper() == 'JR1':
        return jr_one_no_date(request, 'xml', compat=True, requestor_id=requestor_id, requestor_email=requestor_email,
                              requestor_name=requestor_name, customer_ID=customer_ID, customer_name=customer_name,
                              report_request_id=report_request_id)
    elif report_type.upper() == 'JR1GOA':
        return jr_one_goa_no_date(request, 'xml', compat=True, requestor_id=requestor_id,
                                  requestor_email=requestor_email, requestor_name=requestor_name,
                                  customer_ID=customer_ID, customer_name=customer_name,
                                  report_request_id=report_request_id)
    elif report_type.upper() == 'JR2':
        return jr_two_no_date(request, 'xml', compat=True, requestor_id=requestor_id, requestor_email=requestor_email,
                              requestor_name=requestor_name, customer_ID=customer_ID, customer_name=customer_name,
                              report_request_id=report_request_id)


def jr_one_no_date(request, output_format, compat=False, report_request_id='', requestor_id='',
                   requestor_email='', requestor_name='', customer_ID='', customer_name=''):
    start_date = timezone.now() - relativedelta(years=2)
    return jr_one_no_end_date(request, output_format, start_date.year, start_date.month, start_date.day, compat,
                              report_request_id, requestor_id, requestor_email, requestor_name, customer_ID,
                              customer_name)


def jr_one_no_end_date(request, output_format, start_year, start_month, start_day, compat=False, report_request_id='',
                       requestor_id='', requestor_email='', requestor_name='', customer_ID='', customer_name=''):
    return jr_one_all_dates(request, output_format, start_year, start_month, start_day, timezone.now().year,
                            timezone.now().month, timezone.now().day, compat, report_request_id, requestor_id,
                            requestor_email, requestor_name, customer_ID, customer_name)


def jr_one_all_dates(request, output_format, start_year, start_month, start_day, end_year, end_month, end_day,
                     compat=False, report_request_id='', requestor_id='', requestor_email='', requestor_name='',
                     customer_ID='', customer_name=''):
    return jr_one(request, output_format,
                  timezone.datetime(int(start_year), int(start_month), int(start_day),
                                    tzinfo=timezone.get_current_timezone()),
                  timezone.datetime(int(end_year), int(end_month), int(end_day),
                                    tzinfo=timezone.get_current_timezone()),
                  compat, report_request_id, requestor_id, requestor_email, requestor_name, customer_ID,
                  customer_name)


def jr_one(request, output_format, start_date, end_date, compat=False, report_request_id='', requestor_id='',
           requestor_email='', requestor_name='', customer_ID='', customer_name=''):
    """
    Produces COUNTER R1 report in either TSV or XML formats
    :param request: the request object
    :param output_format: the output format ('tsv' or 'xml'). Case insensitive.
    :param start_date: the start date for the report
    :param end_date: the end date for the report
    """

    report_months = [dt for dt in rrule(MONTHLY, dtstart=start_date, until=end_date)]

    press_object = press.models.Press.get_press(request)

    # fetch the metrics
    press_total, press_views, press_downloads, press_months, journals = logic.get_press_totals(start_date,
                                                                                               end_date,
                                                                                               report_months,
                                                                                               compat=compat)

    if output_format.upper() == 'TSV':
        # output a TSV report
        return j1_tsv(start_date, end_date, journals, press_downloads, press_months, press_total, press_views,
                      report_months, request, press_object, 'Journal Report 1(R4)',
                      'Number of Successful Full-text Article Requests by Month and Journal')
    else:
        # output an XML report
        template = 'metrics/counter_jr1.xml'

        # SUSHI COUNTER spec at: http://www.niso.org/apps/group_public/download.php/14101/COUNTER4_1.png
        # unknown variables:
        # vendor_id

        context = {'start_date': start_date.strftime('%Y-%m-%d'),
                   'end_date': end_date.strftime('%Y-%m-%d'),
                   'report_items': journals,
                   'report_created': timezone.now(),
                   'vendor_name': press_object.name,
                   'item_publisher': press_object.name,
                   'vendor_email': press_object.main_contact,
                   'report_ID': report_request_id,
                   'requestor_ID': requestor_id,
                   'requestor_name': requestor_name,
                   'requestor_email': requestor_email,
                   'customer_ID': customer_ID,
                   'customer_name': customer_name}

        return render(request, template, context, content_type='text/xml')


def j1_tsv(start_date, end_date, journals, press_downloads, press_months, press_total, press_views, report_months,
           request, press_object, report_title, report_description):
    """
    COUNTER SPEC:

    Display/Formatting Rules:

    Cell A1 contains the text “Journal Report 1(R4)”
    Cell B1 contains the text “Number of Successful Full-text Article Requests by Month and Journal”
    Cell A2 contains the “Customer” as defined in Appendix A (e.g. “NorthEast Research Library Consortium” or “Yale University”)
    Cell A3 contains the “Institutional Identifier” as defined in Appendix A, but may be left blank if the vendor does not use Institutional Identifiers
    Cell A4 contains the text “Period covered by Report”
    Cell A5 contains the dates that encompass the Period covered by Report in yyyy-mm-dd format. For example a report covering the Period 1 April 2011-30 September 2011 would show 2011-04-01 to 2011-09-30.
    Cell A6 contains the text “Date run”
    Cell A7 contains the date that the report was run in yyyy-mm-dd format. For example, a report run on 12 February 2011 would show 2011-02-12.
    Cell A8 contains the text “Journal”
    Cell B8 contains the text “Publisher”
    Cell C8 contains the text “Platform”
    Cell D8 contains the text “Journal DOI”
    Cell E8 contains the text “Proprietary Identifier”
    Cell F8 contains the text “Print ISSN”
    Cell G8 contains the text “Online ISSN”
    Cell H8 contains the text “Reporting Period Total”
    Cell I8 contains the text “Reporting Period HTML”
    Cell J8 contains the text “Reporting Period PDF”.
    Cell K8 contains the month and year of the first month of data in this report in Mmm-yyyy format. Thus for January 2011, this cell will contain “Jan-2011”
    Cell A9 contains the text “Total for all journals”
    Cell B9 contains the name of the publisher/vendor, provided all the journals listed in column A are from the same publisher/vendor. If not, this cell is left blank.
    Cell C9 contains the name of the platform
    Cells D9, E9, F9 and G9 are blank
    Cell A10 down to Cell A[n] contains the name of each journal
    Cell B10 down to Cell B[n] contains the name of the publisher of each journal
    Cell C10 down to Cell C[n] contains the name of the platform on which each journal is published
    Cell D10 down to Cell D[n] contains the Journal DOI
    Cell E10 down to Cell E[n] contains the Proprietary Identifier, where available
    Cell F10 down to Cell F[n] contains the Print ISSN
    Cell G10 down to Cell G[n] contains the Online ISSN
    Cell H10 down to Cell H[n] contains the number of Full Text Requests Total for the Reporting Period – i.e. the sum of Full Text Requests Total for Jan, Feb etc. up to and including the last reported month.
    Cell I10 down to Cell I[n] contains the number of Full Text HTML Requests Total for the Reporting Period.
    Cell J10 down to Cell J[n] contains the number of Full Text Requests PDF for the Reporting Period.
    Cell K10 down to Cell K[n] contains the number of Full Text Requests for that journal in the corresponding month
    Similarly, Cell L10 down to Cell L[n], Cell M10 down to Cell M[n] etc. contain the Full Text Requests for the corresponding months
    Cell H9 and Cell K9 across to Cell M7 (or whatever column corresponds to the last column of the table) gives totals for each column. The figure reported in these cells in Row 9 must equal the sum of the cells for that column from Row 10 to the bottom of the table.
    """
    row_one, row_two, row_three, row_four, row_five, row_six, row_seven = create_tsv_header(request,
                                                                                            start_date,
                                                                                            end_date,
                                                                                            report_title,
                                                                                            report_description,
                                                                                            press_object)

    row_eight = []
    row_nine = []

    rows = [row_one, row_two, row_three, row_four, row_five, row_six, row_seven, row_eight, row_nine]

    # A8
    row_eight.append('Journal')

    # B8
    row_eight.append('Publisher')

    # C8
    row_eight.append('Platform')

    # D8
    row_eight.append('Journal DOI')

    # E8
    row_eight.append('Proprietary Identifier')

    # F8
    row_eight.append('Print ISSN')

    # G8
    row_eight.append('Online ISSN')

    # H8
    # The game, not the player.
    row_eight.append('Reporting Period Total')

    # I8
    row_eight.append('Reporting Period HTML')

    # J8
    row_eight.append('Reporting Period PDF')

    # K8 -> [X]8
    for date in report_months:
        row_eight.append('{0}-{1}'.format(date.strftime('%b'), date.year))

    # A9
    row_nine.append('Total for all Journals')

    # B9
    row_nine.append(press_object.name)

    # C9
    row_nine.append('Janeway')

    # D9 -> G9
    for x in range(1, 5):
        row_nine.append('')

    # H9
    row_nine.append(press_total)

    # I9
    row_nine.append(press_views)

    # J9
    row_nine.append(press_downloads)

    # K9 -> [X]9
    for date in report_months:
        row_nine.append(press_months['{0}-{1}'.format(date.strftime('%b'), date.year)])

    for journal_dict in journals:
        journal = journal_dict['journal']
        journal_row = [journal.name, press_object.name, 'Janeway', '', '', '', journal.issn,
                       journal_dict['total'], journal_dict['total_views'], journal_dict['total_downloads']]

        for date in report_months:
            journal_row.append(journal_dict['{0}-{1}'.format(date.strftime('%b'), date.year)])

        rows.append(journal_row)

    # Create the HttpResponse object with the appropriate TSV header.
    response = HttpResponse(content_type='text/tsv')
    response['Content-Disposition'] = 'attachment; filename="JR1.tsv"'

    # output the TSV
    writer = csv.writer(response, delimiter='\t')

    for row in rows:
        writer.writerow(row)

    return response


def create_tsv_header(request, start_date, end_date, report_title, report_description, press_object):
    row_one = []
    row_two = []
    row_three = []
    row_four = []
    row_five = []
    row_six = []
    row_seven = []

    # A1
    row_one.append(report_title)

    # B1
    row_one.append(report_description)

    # we interpret Appendix A of the COUNTER specifications to define "Customer" as the Press name, even though
    # they do not pay us for Janeway
    # The formal definition is:
    """
        An individual or organization that pays a vendor for access to a specified range of the vendor’s
        services and/or content and is subject to terms and conditions agreed with the vendor
    """
    # A2
    row_two.append(press_object.name)

    # We do not use institutional identifiers
    # A3
    row_three.append('')

    # A4
    row_four.append('Period covered by Report')

    # A5
    row_five.append('{0}-{1}-{2} to {3}-{4}-{5}'.format(start_date.year,
                                                        start_date.strftime('%m'),
                                                        start_date.strftime('%d'),
                                                        end_date.year,
                                                        end_date.strftime('%m'),
                                                        end_date.strftime('%d')))

    # A6
    row_six.append('Date run')

    # A7
    row_seven.append('{0}-{1}-{2}'.format(timezone.now().year, timezone.now().strftime('%m'),
                                          timezone.now().strftime('%d')))

    return row_one, row_two, row_three, row_four, row_five, row_six, row_seven


def jr_one_goa_no_date(request, output_format, compat=False, report_request_id='', requestor_id='',
                       requestor_email='', requestor_name='', customer_ID='', customer_name=''):
    start_date = timezone.now() - relativedelta(years=2)
    return jr_one_goa_no_end_date(request, output_format, start_date.year, start_date.month, start_date.day, compat,
                                  report_request_id, requestor_id, requestor_email, requestor_name, customer_ID,
                                  customer_name)


def jr_one_goa_no_end_date(request, output_format, start_year, start_month, start_day, compat=False,
                           report_request_id='', requestor_id='', requestor_email='', requestor_name='',
                           customer_ID='', customer_name=''):
    return jr_one_goa_all_dates(request, output_format, start_year, start_month, start_day, timezone.now().year,
                                timezone.now().month, timezone.now().day, compat, report_request_id, requestor_id,
                                requestor_email, requestor_name, customer_ID, customer_name)


def jr_one_goa_all_dates(request, output_format, start_year, start_month, start_day, end_year, end_month, end_day,
                         compat=False, report_request_id='', requestor_id='', requestor_email='', requestor_name='',
                         customer_ID='', customer_name=''):
    return jr_one_goa(request, output_format,
                      timezone.datetime(int(start_year), int(start_month), int(start_day),
                                        tzinfo=timezone.get_current_timezone()),
                      timezone.datetime(int(end_year), int(end_month), int(end_day),
                                        tzinfo=timezone.get_current_timezone()),
                      compat, report_request_id, requestor_id, requestor_email, requestor_name, customer_ID,
                      customer_name)


def jr_one_goa(request, output_format, start_date, end_date, compat=False, report_request_id='', requestor_id='',
               requestor_email='', requestor_name='', customer_ID='', customer_name=''):
    """
    Produces COUNTER JR1 GOA report in either TSV or XML formats
    :param request: the request object
    :param output_format: the output format ('tsv' or 'xml'). Case insensitive.
    :param start_date: the start date for the report
    :param end_date: the end date for the report
    """

    report_months = [dt for dt in rrule(MONTHLY, dtstart=start_date, until=end_date)]

    press_object = press.models.Press.get_press(request)

    # fetch the metrics
    press_total, press_views, press_downloads, press_months, journals = logic.get_press_totals(start_date,
                                                                                               end_date,
                                                                                               report_months,
                                                                                               compat=compat)

    if output_format.upper() == 'TSV':
        # output a TSV report
        return j1_tsv(start_date, end_date, journals, press_downloads, press_months, press_total, press_views,
                      report_months, request, press_object, 'Journal Report 1 GOA (R4)',
                      'Number of Successful Gold Open Access Full-Text Article Requests by Month and Journal')
    else:
        # output an XML report
        template = 'metrics/counter_jr1_goa.xml'

        # SUSHI COUNTER spec at: http://www.niso.org/apps/group_public/download.php/14101/COUNTER4_1.png
        # unknown variables:
        # vendor_id

        context = {'start_date': start_date.strftime('%Y-%m-%d'),
                   'end_date': end_date.strftime('%Y-%m-%d'),
                   'report_items': journals,
                   'report_created': timezone.now(),
                   'vendor_name': press_object.name,
                   'item_publisher': press_object.name,
                   'vendor_email': press_object.main_contact,
                   'report_ID': report_request_id,
                   'requestor_ID': requestor_id,
                   'requestor_name': requestor_name,
                   'requestor_email': requestor_email,
                   'customer_ID': customer_ID,
                   'customer_name': customer_name}

        return render(request, template, context, content_type='text/xml')


def jr_two_no_date(request, output_format, compat=False, report_request_id='', requestor_id='',
                   requestor_email='', requestor_name='', customer_ID='', customer_name=''):
    start_date = timezone.now() - relativedelta(years=2)
    return jr_two_no_end_date(request, output_format, start_date.year, start_date.month, start_date.day, compat,
                              report_request_id, requestor_id, requestor_email, requestor_name, customer_ID,
                              customer_name)


def jr_two_no_end_date(request, output_format, start_year, start_month, start_day, compat=False, report_request_id='',
                       requestor_id='', requestor_email='', requestor_name='', customer_ID='', customer_name=''):
    return jr_two_all_dates(request, output_format, start_year, start_month, start_day, timezone.now().year,
                            timezone.now().month, timezone.now().day, compat, report_request_id, requestor_id,
                            requestor_email, requestor_name, customer_ID, customer_name)


def jr_two_all_dates(request, output_format, start_year, start_month, start_day, end_year, end_month, end_day,
                     compat=False, report_request_id='', requestor_id='', requestor_email='', requestor_name='',
                     customer_ID='', customer_name=''):
    return jr_two(request, output_format,
                  timezone.datetime(int(start_year), int(start_month), int(start_day),
                                    tzinfo=timezone.get_current_timezone()),
                  timezone.datetime(int(end_year), int(end_month), int(end_day),
                                    tzinfo=timezone.get_current_timezone()),
                  compat, report_request_id, requestor_id, requestor_email, requestor_name, customer_ID,
                  customer_name)


def jr_two(request, output_format, start_date, end_date, compat=False, report_request_id='', requestor_id='',
           requestor_email='', requestor_name='', customer_ID='', customer_name=''):
    """
    Produces COUNTER JR1 GOA report in either TSV or XML formats
    :param request: the request object
    :param output_format: the output format ('tsv' or 'xml'). Case insensitive.
    :param start_date: the start date for the report
    :param end_date: the end date for the report
    """

    report_months = [dt for dt in rrule(MONTHLY, dtstart=start_date, until=end_date)]

    press_object = press.models.Press.get_press(request)

    # fetch the metrics
    press_total, press_views, press_downloads, press_months, journals = logic.get_press_totals(start_date,
                                                                                               end_date,
                                                                                               report_months,
                                                                                               compat=compat)

    if output_format.upper() == 'TSV':
        # output a TSV report
        return j2_tsv(start_date, end_date, journals, report_months, request, press_object, 'Journal Report 2 (R4)',
                      'Access Denied to Full-text Articles by Month, Journal and Category')
    else:
        # output an XML report
        template = 'metrics/counter_jr2.xml'

        # SUSHI COUNTER spec at: http://www.niso.org/apps/group_public/download.php/14101/COUNTER4_1.png
        # unknown variables:
        # vendor_id

        context = {'start_date': start_date.strftime('%Y-%m-%d'),
                   'end_date': end_date.strftime('%Y-%m-%d'),
                   'report_items': journals,
                   'report_created': timezone.now(),
                   'vendor_name': press_object.name,
                   'item_publisher': press_object.name,
                   'vendor_email': press_object.main_contact,
                   'report_ID': report_request_id,
                   'requestor_ID': requestor_id,
                   'requestor_name': requestor_name,
                   'requestor_email': requestor_email,
                   'customer_ID': customer_ID,
                   'customer_name': customer_name}

        return render(request, template, context, content_type='text/xml')


def j2_tsv(start_date, end_date, journals, report_months, request, press_object, report_title, report_description):

    row_one, row_two, row_three, row_four, row_five, row_six, row_seven = create_tsv_header(request,
                                                                                            start_date,
                                                                                            end_date,
                                                                                            report_title,
                                                                                            report_description,
                                                                                            press_object)

    row_eight = []
    row_nine = []
    row_ten = []

    rows = [row_one, row_two, row_three, row_four, row_five, row_six, row_seven, row_eight, row_nine, row_ten]

    # A8
    row_eight.append('Journal')

    # B8
    row_eight.append('Publisher')

    # C8
    row_eight.append('Platform')

    # D8
    row_eight.append('Journal DOI')

    # E8
    row_eight.append('Proprietary Identifier')

    # F8
    row_eight.append('Print ISSN')

    # G8
    row_eight.append('Online ISSN')

    # H8
    # The game, not the player.
    row_eight.append('Access Denied Category')

    # I8
    row_eight.append('Reporting Period Total')

    # J8 -> [X]8
    for date in report_months:
        row_eight.append('{0}-{1}'.format(date.strftime('%b'), date.year))

    # A9
    row_nine.append('Total for all Journals')

    # B9
    row_nine.append(press_object.name)

    # C9
    row_nine.append('Janeway')

    # D9 -> G9
    for x in range(1, 5):
        row_nine.append('')

    # H9
    row_nine.append('Access denied: concurrent/simultaneous user license limit exceeded')

    # I9
    row_nine.append(0)

    # J9 -> [X]9
    for date in report_months:
        row_nine.append(0)

    # A10
    row_ten.append('Total for all Journals')

    # B10
    row_ten.append(press_object.name)

    # C1-
    row_ten.append('Janeway')

    # D10 -> G10
    for x in range(1, 5):
        row_ten.append('')

    # H10
    row_ten.append('Access denied: content item not licensed')

    # I10
    row_ten.append(0)

    # J10 -> [X]10
    for date in report_months:
        row_ten.append(0)

    for journal_dict in journals:
        journal = journal_dict['journal']
        journal_row = [journal.name, press_object.name, 'Janeway', '', '', '', journal.issn,
                       'Access denied: concurrent/simultaneous user license limit exceeded', 0]

        for date in report_months:
            journal_row.append(0)

        rows.append(journal_row)

        journal_row_two = [journal.name, press_object.name, 'Janeway', '', '', '', journal.issn,
                           'Access denied: content item not licensed', 0]

        for date in report_months:
            journal_row_two.append(0)

        rows.append(journal_row_two)

    # Create the HttpResponse object with the appropriate TSV header.
    response = HttpResponse(content_type='text/tsv')
    response['Content-Disposition'] = 'attachment; filename="JR2.tsv"'

    # output the TSV
    writer = csv.writer(response, delimiter='\t')

    for row in rows:
        writer.writerow(row)

    return response


def j5_tsv(start_date, end_date, journals, yops, request, press_object, report_title, report_description):

    row_one, row_two, row_three, row_four, row_five, row_six, row_seven = create_tsv_header(request,
                                                                                            start_date,
                                                                                            end_date,
                                                                                            report_title,
                                                                                            report_description,
                                                                                            press_object)

    row_eight = []
    row_nine = []
    row_ten = []

    rows = [row_one, row_two, row_three, row_four, row_five, row_six, row_seven, row_eight, row_nine, row_ten]

    # A8
    row_eight.append('Journal')

    # B8
    row_eight.append('Publisher')

    # C8
    row_eight.append('Platform')

    # D8
    row_eight.append('Journal DOI')

    # E8
    row_eight.append('Proprietary Identifier')

    # F8
    row_eight.append('Print ISSN')

    # G8
    row_eight.append('Online ISSN')

    # H8
    # The game, not the player.
    row_eight.append('Articles in Press')

    # I8 -> [X]8
    for year in yops:
        row_eight.append('YOP {0}'.format(yops[year]))

    # A9
    row_nine.append('Total for all Journals')

    # B9
    row_nine.append(press_object.name)

    # C9
    row_nine.append('Janeway')

    # D9 -> G9
    for x in range(1, 5):
        row_nine.append('')

    # H9
    row_nine.append('Access denied: concurrent/simultaneous user license limit exceeded')

    # I9
    row_nine.append(0)

    # J9 -> [X]9
    for date in report_months:
        row_nine.append(0)

    # A10
    row_ten.append('Total for all Journals')

    # B10
    row_ten.append(press_object.name)

    # C1-
    row_ten.append('Janeway')

    # D10 -> G10
    for x in range(1, 5):
        row_ten.append('')

    # H10
    row_ten.append('Access denied: content item not licensed')

    # I10
    row_ten.append(0)

    # J10 -> [X]10
    for date in report_months:
        row_ten.append(0)

    for journal_dict in journals:
        journal = journal_dict['journal']
        journal_row = [journal.name, press_object.name, 'Janeway', '', '', '', journal.issn,
                       'Access denied: concurrent/simultaneous user license limit exceeded', 0]

        for date in report_months:
            journal_row.append(0)

        rows.append(journal_row)

        journal_row_two = [journal.name, press_object.name, 'Janeway', '', '', '', journal.issn,
                           'Access denied: content item not licensed', 0]

        for date in report_months:
            journal_row_two.append(0)

        rows.append(journal_row_two)

    # Create the HttpResponse object with the appropriate TSV header.
    response = HttpResponse(content_type='text/tsv')
    response['Content-Disposition'] = 'attachment; filename="JR2.tsv"'

    # output the TSV
    writer = csv.writer(response, delimiter='\t')

    for row in rows:
        writer.writerow(row)

    return response
