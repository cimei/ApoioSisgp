from project import app
from flask import render_template
import webbrowser
from threading import Timer

@app.route('/')
def index():
    return render_template('home.html')

def open_browser():
    webbrowser.open_new('http://127.0.0.1:5000/')

if __name__ == '__main__':
    Timer(1, open_browser).start();
    app.run(port=5000)
