#!/usr/local/bin/python

import re, sys, urllib2
import argparse 
import arrow # http://crsmithdev.com/arrow/
import pypandoc # https://github.com/bebraw/pypandoc
from bs4 import BeautifulSoup
from itertools import cycle

parser = argparse.ArgumentParser()
parser.add_argument('semester', help='Spring or Fall')
parser.add_argument('year', type=int, help='Year as YYYY')
parser.add_argument('days', help='String of class days as MTWRF')
parser.add_argument('--verbose', action='store_true', help='Show cancelled classes in output')
args = parser.parse_args()

def check_args():
    checks = []
    checks.append(set(args.days + 'MTWRF') != set('MTWRF'))
    checks.append(args.semester.lower() not in ['spring','fall'])
    if True in checks:
        print 'Input error in your arguments.'
        parser.print_help()
        sys.exit(1)
    if args.year < 2009:
        print 'ERROR: The script only works for the years 2009 to the present.'
        sys.exit(1)

def locale():
    return arrow.locales.get_locale('en_us')

def regex(keyword):
    return re.compile('(.*)' + keyword + '(.*)', re.DOTALL)

def url(sem, year): 
    baseurl = 'https://registrar.rice.edu/calendars/'
    return baseurl + sem.lower() + year[-2:] + '/'

def fetch_registrar_table(url):
    ''' Get academic calendar table from registrar website '''
    html = urllib2.urlopen(url).read()
    soup = BeautifulSoup(html, 'html.parser')
    return soup.find('table')

def range_of_days(start, end):
    return arrow.Arrow.range('day', start, end)

def clean_cell(td):
    ''' Remove whitespace from a registrar table cell '''
    return re.sub(r"\s+", "", td, flags=re.UNICODE)

def parse_td_for_dates(td):
    ''' Get date or date range as lists from cell in registrar's table '''
    cell = clean_cell(td)
    months = ['January', 'February', 'March', 'April', 'May',
            'June', 'July', 'August', 'September', 'October', 'November', 'December']
    ms = [locale().month_number(m) for m in months if m in cell]
    ds = [int(d) for d in re.split('\D', cell) if 0 < len(d) < 3]
    ys = [int(y) for y in re.split('\D', cell) if len(y) == 4]
    dates = zip(cycle(ms), ds) if len(ds) > len(ms) else zip(ms, ds)
    dates = [arrow.get(ys[0], md[0], md[1]) for md in dates]
    if len(dates) > 1:
        return range_of_days(dates[0], dates[1])
    else:
        return dates

def parse_registrar_table(table):
    ''' Parse registrar table and return first, last, cancelled days of class as lists '''
    no_classes = []
    for row in table.findAll('tr'):
        cells = row.findAll('td')
        days = clean_cell(cells[0].get_text())
        try:
            description = cells[1].get_text()
        except:
            pass
        if re.match(regex('FIRST DAY OF CLASSES'), description):
            first_day = parse_td_for_dates(days)
        if re.match(regex('LAST DAY OF CLASSES'), description):
            last_day = parse_td_for_dates(days)
        for date in parse_td_for_dates(days):
            if re.match(regex('NO SCHEDULED CLASSES'), description):
                no_classes.append(date)
    return first_day, last_day, no_classes

def sorted_classes(weekdays):
    ''' Take class meetings as list of day names, return lists of Arrow objects '''
    first_day, last_day, no_classes = parse_registrar_table(fetch_registrar_table(url))
    semester = range_of_days(first_day[0], last_day[0])
    possible_classes = [d for d in semester if locale().day_name(d.isoweekday()) in weekdays]
    return possible_classes, no_classes

def schedule(possible_classes, no_classes, fmt, show_no=None):
    ''' Take lists of Arrow objects, return list of course meetings as strings '''
    course = []
    for d in possible_classes:
        if d not in no_classes:
            course.append(d.format(fmt))
        elif show_no:
            course.append(d.format(fmt) + ' - NO CLASS')
    return course

def output_plain(schedule):
    print '\n'.join(schedule)

def output_docx(schedule, args):
    course = ['## ' + d + '\n' for d in schedule]
    course = [d + '[Fill in class plan]\n\n' if 'NO CLASS' not in d else d for d in course]
    md_args = ['--template=./templates/syllabus.md', '--to=markdown',
            '--variable=semester:' + args.semester.capitalize(), '--variable=year:' + str(args.year)]
    md_output = pypandoc.convert('\n'.join(course), 'md', 'md', md_args)
    docx_args = ['--reference-docx=./templates/syllabus.docx']
    docx_output = pypandoc.convert(md_output, 'docx', 'md', docx_args, outputfile='output.docx')
    assert docx_output == ''

check_args()
url = url(args.semester, str(args.year))
day_index = {'M': 'Monday', 'T': 'Tuesday', 'W': 'Wednesday', 'R': 'Thursday', 'F': 'Friday'}
possible_classes, no_classes = sorted_classes([day_index[d] for d in args.days])
output_docx(schedule(possible_classes, no_classes, 'dddd, MMMM D, YYYY', args.verbose), args)
