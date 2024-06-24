from flask import Flask, render_template, request, redirect, url_for
import os
import time
import subprocess
#import pdb; pdb.set_trace()

app = Flask(__name__)

# Initialize the relay statuses
relays = [False, False, False, False]

# Function to check if the remote host is online
def is_host_online(hostname):
    response = subprocess.run(['ping', '-c', '1', hostname], stdout=subprocess.DEVNULL)
    return response.returncode == 0

# Function to execute a command via SSH using os.system
def execute_remote_command(script_name):
    hostname = '192.168.0.127'
    max_attempts = 5
    for attempt in range(max_attempts):
        if is_host_online(hostname):
            ssh_command = f'ssh pi@{hostname} sudo /home/pi/{script_name}'
            os.system(ssh_command)
            return True
        else:
            time.sleep(60)  # Wait for 1 minute before retrying
    return False

# Function to get relay statuses from the remote host
def get_relay_statuses():
    hostname = '192.168.0.127'
    if is_host_online(hostname):
        ssh_command = f'ssh pi@{hostname} sudo bash /home/pi/get_relay_statuses.sh"'
        result = subprocess.run(ssh_command, shell=True, capture_output=True, text=True)
        print('Result - ', result.stdout)
        result_std = result.stdout
        print('Result_std - ', result_std)
        print(ssh_command)
        if result.returncode == 0:
            statuses = result.stdout.strip().split()
            print('statuses - ', statuses)
#            breakpoint()
            for i in range(4):
                if statuses[i] == '0xff':
                    relays[i] = True
                if statuses[i] == '0x00':
                    relays[i] = False
                print('statuses - ', statuses[i])
#                return [relays == '0x01' for status in statuses]
    return [relays[0],relays[1],relays[2],relays[3]]

@app.route('/')
def index():
    return render_template('index.html', relays=relays)

@app.route('/update_relay', methods=['POST'])
def update_relay():
    relay_id = int(request.form['relay_id'])
    action = request.form['action']
    
    if action == 'on':
        relays[relay_id] = True
        # Execute remote script to turn relay on
        success = execute_remote_command(f'relay{relay_id}-on.sh')
    else:
        relays[relay_id] = False
        # Execute remote script to turn relay off
        success = execute_remote_command(f'relay{relay_id}-off.sh')

    if not success:
        return "Failed to reach the host after multiple attempts", 500
    
    return redirect(url_for('index'))

@app.route('/refresh_status', methods=['POST'])
def refresh_status():
    global relays
    relays = get_relay_statuses()
    return redirect(url_for('index'))

if __name__ == '__main__':
    relays = get_relay_statuses()
    app.run(debug=True)

