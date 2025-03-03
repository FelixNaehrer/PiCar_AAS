import paramiko
import subprocess
from werkzeug.serving import make_server
from flaskServer import app
from opc_ua_consumer import OpcUaThread
import threading
import atexit
import time
import socket

# Raspberry Pi-Verbindungsdetails
RASPBERRY_PI_IP = "172.20.10.2"
RASPBERRY_PI_USER = "felix_naehrer"
RASPBERRY_PI_PASSWORD = "felix_naehrer"  # Kann leer sein, wenn Schlüssel verwendet wird
SSH_KEY_PATH = None  # Beispiel: "/path/to/your/private_key"
REMOTE_SCRIPT = "/home/felix_naehrer/SunFounder_PiCar-S/example/opc_ua_server.py"
OPC_UA_SERVER_PORT = 4840  # Port of the OPC UA server

class FlaskThread(threading.Thread):
    """Thread für den Flask-Server."""
    def __init__(self):
        super().__init__()
        self.server = make_server("0.0.0.0", 1080, app)
        self.ctx = app.app_context()
        self.ctx.push()
        self.shutdown_event = threading.Event()

    def run(self):
        print("Starting Flask server...")
        try:
            while not self.shutdown_event.is_set():
                self.server.handle_request()
        except Exception as e:
            print(f"Flask server error: {e}")

    def shutdown(self):
        print("Shutting down Flask server...")
        self.shutdown_event.set()
        self.server.shutdown()


def start_remote_script():
    """Startet das Skript `opc_ua_server.py` auf dem Raspberry Pi über SSH."""
    print("Starting remote OPC UA server script on Raspberry Pi...")
    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())  # Automatisch unbekannte Hosts akzeptieren

        if SSH_KEY_PATH:
            print("Using key-based authentication...")
            ssh.connect(
                hostname=RASPBERRY_PI_IP,
                username=RASPBERRY_PI_USER,
                key_filename=SSH_KEY_PATH,
                timeout=10,
            )
        elif RASPBERRY_PI_PASSWORD:
            print("Using password-based authentication...")
            ssh.connect(
                hostname=RASPBERRY_PI_IP,
                username=RASPBERRY_PI_USER,
                password=RASPBERRY_PI_PASSWORD,
                timeout=10,
            )
        else:
            raise Exception("No valid authentication method provided.")

        command = f"nohup python3 {REMOTE_SCRIPT} > /tmp/opc_ua_server.log 2>&1 & echo $!"
        stdin, stdout, stderr = ssh.exec_command(command)
        pid = stdout.read().decode().strip()
        print(f"Remote script started with PID {pid}.")

        stderr_output = stderr.read().decode().strip()
        if stderr_output:
            raise Exception(f"Error starting remote script: {stderr_output}")

        return pid
    except Exception as e:
        print(f"Failed to start remote script: {e}")
        return None
    finally:
        ssh.close()
        print("SSH connection closed.")


def stop_remote_script(pid):
    """Beendet das Skript `opc_ua_server.py` auf dem Raspberry Pi."""
    print(f"Stopping remote script with PID {pid} on Raspberry Pi...")
    try:
        command = f"kill {pid}"
        subprocess.run(
            ["ssh", f"{RASPBERRY_PI_USER}@{RASPBERRY_PI_IP}", command],
            check=True
        )
        print("Remote script stopped.")
    except Exception as e:
        print(f"Failed to stop remote script: {e}")


def wait_for_opc_ua_server(ip, port, timeout=60):
    """Warte, bis der OPC UA-Server verfügbar ist."""
    print(f"Waiting for OPC UA server at {ip}:{port} to become available...")
    start_time = time.time()
    while time.time() - start_time < timeout:
        try:
            with socket.create_connection((ip, port), timeout=5):
                print("OPC UA server is available.")
                return True
        except (socket.timeout, ConnectionRefusedError):
            time.sleep(1)
    print(f"OPC UA server not available after {timeout} seconds.")
    return False

if __name__ == "__main__":
    print("Middleware server started...")

    remote_script_pid = start_remote_script()
    if not remote_script_pid:
        print("Exiting due to failure to start remote OPC UA server.")
        exit(1)

    if not wait_for_opc_ua_server(RASPBERRY_PI_IP, OPC_UA_SERVER_PORT):
        print("Exiting due to unavailable OPC UA server.")
        stop_remote_script(remote_script_pid)
        exit(1)

    flask_thread = FlaskThread()
    flask_thread.start()

    opcua_thread = OpcUaThread()
    opcua_thread.daemon = True  # Ensure thread stops when main program exits
    opcua_thread.start()

    @atexit.register
    def cleanup():
        print("Cleaning up resources...")
        if flask_thread.is_alive():
            flask_thread.shutdown()
            flask_thread.join()
        if opcua_thread.is_alive():
            print("Stopping OPC UA Consumer...")
            opcua_thread.join(timeout=1)
        if remote_script_pid:
            stop_remote_script(remote_script_pid)
        print("Cleanup complete.")

    try:
        while flask_thread.is_alive() or opcua_thread.is_alive():
            time.sleep(1)
    except KeyboardInterrupt:
        print("Interrupt received, shutting down...")

    print("Middleware server stopped.")
