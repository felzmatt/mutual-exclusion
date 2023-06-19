from flask import Flask, render_template, request

app = Flask(__name__)

@app.route('/', methods=['GET'])
def index():
    return render_template('index.html')

@app.route('/enter_cs', methods=['POST'])
def enter_cs():
    # Access the data sent in the POST request
    data = request.form
    key = data.get('key')  # Access a specific value by key

    # Handle the data as needed
    # Perform any necessary processing or database operations
    # Return an appropriate response

    return "Entered the CS"

@app.route('/leave_cs', methods=['POST'])
def leave_cs():
    # Access the data sent in the POST request
    data = request.form
    key = data.get('key')  # Access a specific value by key

    # Handle the data as needed
    # Perform any necessary processing or database operations
    # Return an appropriate response

    return "Left the CS"

if __name__ == '__main__':
    app.run()
