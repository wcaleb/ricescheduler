#!/usr/bin/env python

import os
from flask import Flask, render_template, request, url_for, send_file
from tempfile import NamedTemporaryFile
from ricescheduler import make_url, sorted_classes, schedule, output, date_formats

app = Flask(__name__, static_url_path = "")

@app.route('/')
def form():
    years = [str(y) for y in range(2009,2017)][::-1]
    formats = [t[0] for t in date_formats()]
    return render_template('form_submit.html', years=years, formats=formats)

@app.route('/results/', methods=['POST'])
def results():

    semester = request.form['semester']
    year = request.form['year']
    weekdays = request.form.getlist('days')
    date_fmt = [b for (a, b) in date_formats() if a == request.form['format']][0]
    output_fmt = request.form['output']

    url = make_url(semester, year)
    possible_classes, no_classes = sorted_classes(weekdays, url)
    course = schedule(possible_classes, no_classes, show_no=True, fmt=date_fmt) 

    if output_fmt == 'plain':
        return '<br/>'.join(course)
    else:
        suffix = '.' + output_fmt
        templatedir = os.path.dirname(os.path.abspath(__file__)) + '/templates'
        tf = NamedTemporaryFile(suffix=suffix)
        output(course, semester, year, output_fmt, templatedir=templatedir, outfile=tf.name)
        filename = semester + year + 'Syllabus' + suffix
        return send_file(tf.name, attachment_filename=filename, as_attachment=True)

if __name__ == '__main__':
    app.run()
