import os
from flask import Flask, render_template, request, jsonify

app = Flask(__name__)

NUM = int(os.getenv("NUM_PROC"))
DES_ACCESSES = int(os.getenv("DES_ACCESSES"))

# state of critical section variables
processesCS = [0 for i in range(NUM)]
tot_accesses = [0 for i in range(NUM)]
inside = 0
errors = 0

@app.route('/', methods=['GET'])
def index():
    return render_template('index.html')

@app.route('/init')
def init_data():
    data = {
        'num_processes': NUM,
        'des_accesses': DES_ACCESSES,
        'tot_accesses': list(tot_accesses)
    }
    return jsonify(data)


@app.route('/data')
def get_data():
    # Replace with your logic to fetch the actual values for processes and errors
    global errors

    data = {
        'processes': list(processesCS),
        'errors': errors,
        'tot_accesses': tot_accesses
    }
    return jsonify(data)

@app.route('/enter_cs', methods=['POST'])
def enter_cs():
    # Access the data sent in the POST request
    global errors
    global inside
    data = request.form
    procID = data.get('procID')  # Access a specific value by key
    processesCS[int(procID) - 1] += 1
    tot_accesses[int(procID) - 1] += 1
    inside += 1
    if inside > 1:
        errors += 1

    # Handle the data as needed
    # Perform any necessary processing or database operations
    # Return an appropriate response

    return "Entered the CS"

@app.route('/leave_cs', methods=['POST'])
def leave_cs():
    # Access the data sent in the POST request
    global errors
    global inside
    data = request.form
    procID = data.get('procID')  # Access a specific value by key
    processesCS[int(procID) - 1] -= 1
    inside -= 1

    # Handle the data as needed
    # Perform any necessary processing or database operations
    # Return an appropriate response

    return "Left the CS"

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000)
