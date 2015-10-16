from flask import Flask, render_template, request, url_for, send_file
import ricescheduler

app = Flask(__name__, static_url_path = "")

@app.route('/')
def form():
    years = [str(y) for y in range(2009,2017)]
    return render_template('form_submit.html', years=years)

@app.route('/output/', methods=['POST', 'GET'])
def classes():
    semester = request.form['semester']
    year = request.form['year']
    weekdays = request.form.getlist('days')
    url = ricescheduler.url(semester, year)
    possible_classes, no_classes = ricescheduler.sorted_classes(weekdays, url)
    schedule = ricescheduler.schedule(possible_classes, no_classes, 'dddd, MMMM D, YYYY') 
    return '<br/>'.join(schedule) 

if __name__ == '__main__':
    app.run(debug=True)
