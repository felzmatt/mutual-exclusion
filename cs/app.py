import os
from datetime import datetime

from flask import Flask, render_template, request, jsonify, send_file

from events import EventType, Event, EventRegister

def generate_timestamp():
    current_datetime = datetime.now()
    timestamp = current_datetime.strftime("%Y%m%d_%H%M")
    return timestamp

app = Flask(__name__)

NUM = int(os.getenv("NUM_PROC"))
# DES_ACCESSES = int(os.getenv("DES_ACCESSES"))

# DOWNLOAD = False

# This class contains data that will be flushed into a csv file for analysys
events_register = EventRegister()

# state of critical section variables
processesCS = [0 for i in range(NUM)]
tot_accesses = [0 for i in range(NUM)]
inside = 0
errors = 0

result_file = f"{generate_timestamp()}_exp.csv"

@app.route('/', methods=['GET'])
def index():
    return render_template('index.html')

@app.route('/init')
def init_data():
    data = {
        'num_processes': NUM,
        # 'des_accesses': DES_ACCESSES,
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
        'tot_accesses': tot_accesses,
        # 'download': DOWNLOAD
    }
    return jsonify(data)

@app.route('/enter_cs', methods=['POST'])
def enter_cs():
    # Access the data sent in the POST request
    global errors
    global inside
    data = request.form
    procID = data.get('procID')  # Access a specific value by key
    if processesCS[int(procID) - 1] == 0:
        processesCS[int(procID) - 1] += 1
        tot_accesses[int(procID) - 1] += 1
        inside += 1
        if inside > 1:
            errors += 1
            events_register.insert_event(
                Event(evtype=EventType.ACCESS, procID=procID, anomaly=True)
            )
        else:
            events_register.insert_event(
                Event(evtype=EventType.ACCESS, procID=procID, anomaly=False)
            )
        """
        if all([x >= DES_ACCESSES for x in tot_accesses]):
            global DOWNLOAD
            DOWNLOAD = True
        """
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
    events_register.insert_event(
        Event(evtype=EventType.LEAVE, procID=procID, anomaly=False)
    )
    return "Left the CS"

@app.route('/results_file')
def download_results():
    # flush the content of the event register into a csv file and send
    # to the browser for download
    events_register.close_register()
    events_register.write_on_csv(result_file)
    filepath = os.path.join(os.getcwd(), result_file)
    return send_file(filepath, as_attachment=True, download_name=result_file)



if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000)
