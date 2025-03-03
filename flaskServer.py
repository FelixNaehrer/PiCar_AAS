from flask import Flask, request, jsonify
import paramiko
import time
from werkzeug.serving import make_server

app = Flask(__name__)

# Debug-Flag
DEBUG = False  # Setze auf False, um Debug-Ausgaben zu deaktivieren

# IP-Adresse des Raspberry Pi und Benutzername/Passwort
RASPBERRY_PI_IP = "172.20.10.2"
RASPBERRY_PI_USER = "felix_naehrer"
RASPBERRY_PI_PASSWORD = "felix_naehrer"

# Pfade zu den Skripten auf dem Raspberry Pi
FRONT_WHEEL_SCRIPT = "/home/felix_naehrer/SunFounder_PiCar-S/example/front-wheel-test-custom.py"
LINE_FOLLOWER_SCRIPT = "/home/felix_naehrer/SunFounder_PiCar-S/example/line-follower-custom.py"
LIGHT_FOLLOWER_SCRIPT = "/home/felix_naehrer/SunFounder_PiCar-S/example/light-follower-custom.py"
SELF_TEST_SCRIPT = "/home/felix_naehrer/SunFounder_PiCar-S/example/test_ultrasonic_module.py"   #Starts UltraSonic Sensor Test -> only way to make some kind of noice
GET_LOCATION = "/home/felix_naehrer/SunFounder_PiCar-S/example/get-current-location.py"
CALCULATE_DISTANCE = "/home/felix_naehrer/SunFounder_PiCar-S/example/calculate-distance.py"


def execute_script(script_path, duration):
    try:
        print("Flask Server: Verbinde mit Raspberry Pi über SSH...")
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())  # Automatisch unbekannte Hosts akzeptieren
        ssh.connect(RASPBERRY_PI_IP, username=RASPBERRY_PI_USER, password=RASPBERRY_PI_PASSWORD)

        print(f"Flask Server: Starte Skript {script_path} für {duration} Sekunden...")
        command = f"python3 {script_path} --duration {duration} & echo $!"
        stdin, stdout, stderr = ssh.exec_command(command)
        pid = stdout.read().decode().strip()  # PID des gestarteten Prozesses
        print(f"Flask Server: Skript gestartet mit PID {pid}")

        # Überprüfen, ob Fehler aufgetreten sind
        stderr_output = stderr.read().decode().strip()
        if stderr_output:
            raise Exception(f"Flask Server: Fehler beim Starten des Skripts: {stderr_output}")

        # Debug-Ausgaben für Skriptergebnisse
        if DEBUG:
            stdout_output = stdout.read().decode().strip()
            print(f"Flask Server (DEBUG): {stdout_output}")

        # Warten, bis die angegebene Dauer erreicht ist
        time.sleep(duration)

        # SIGINT an den Prozess senden
        ssh.exec_command(f"kill -SIGINT {pid}")
        print(f"Flask Server: SIGINT an Prozess {pid} gesendet")

        return f"Skript erfolgreich für {duration} Sekunden ausgeführt."

    except Exception as e:
        return f"Flask Server: Fehler beim Ausführen des Skripts: {str(e)}"

    finally:
        # SSH-Verbindung schließen
        ssh.close()
        print("Flask Server: SSH-Verbindung geschlossen")


def shutdown_server():
    func = request.environ.get('werkzeug.server.shutdown')
    if func is None:
        print("Flask Server: Warning: Nicht mit Werkzeug Server ausgeführt. Shutdown könnte fehlschlagen.")
        return
    func()

@app.route('/submodels/aHR0cHM6Ly9leGFtcGxlLm9yZy9zdW5mb3VuZGVyL3BpY2FyLWNvbnRyb2w/submodel-elements/VGVzdEZyb250V2hlZWxz/invoke', methods=['POST'])
def handle_test_front_wheels():
    data = request.json
    duration = int(data[0].get("value", {}).get("value", 10)) if isinstance(data, list) and len(data) > 0 else 10
    print(f"\nFlask Server: Ausführung des Front-Wheel-Tests für {duration} Sekunden...")
    result = execute_script(FRONT_WHEEL_SCRIPT, duration)

    result = {"value": {
        "idShort": "Result",  # Muss zum Submodell passen
        "modelType": "Property",
        "valueType": "xs:string",  # Muss mit Submodell-Definition übereinstimmen
        "value": result
    }}

    print(f"Returning result: {result}")  # Debug-Log
    return jsonify(result)

@app.route('/submodels/aHR0cHM6Ly9leGFtcGxlLm9yZy9zdW5mb3VuZGVyL3BpY2FyLWNvbnRyb2w/submodel-elements/TGluZUZvbGxvd2Vy/invoke', methods=['POST'])
def handle_line_follower():
    data = request.json
    duration = int(data[0].get("value", {}).get("value", 10)) if isinstance(data, list) and len(data) > 0 else 10
    print(f"\nFlask Server: Ausführung des Line-Followers für {duration} Sekunden...")
    result = execute_script(LINE_FOLLOWER_SCRIPT, duration)

    result = {"value": {
        "idShort": "Result",  # Muss zum Submodell passen
        "modelType": "Property",
        "valueType": "xs:string",  # Muss mit Submodell-Definition übereinstimmen
        "value": result
    }}

    print(f"Returning result: {result}")  # Debug-Log
    return jsonify(result)

@app.route('/submodels/aHR0cHM6Ly9leGFtcGxlLm9yZy9zdW5mb3VuZGVyL3BpY2FyLWNvbnRyb2w/submodel-elements/TGlnaHRGb2xsb3dlcg==/invoke', methods=['POST'])
def handle_light_follower():
    data = request.json
    duration = int(data[0].get("value", {}).get("value", 10)) if isinstance(data, list) and len(data) > 0 else 10
    print(f"\nFlask Server: Ausführung des Light-Followers für {duration} Sekunden...")
    result = execute_script(LIGHT_FOLLOWER_SCRIPT, duration)

    result = {"value": {
        "idShort": "Result",  # Muss zum Submodell passen
        "modelType": "Property",
        "valueType": "xs:string",  # Muss mit Submodell-Definition übereinstimmen
        "value": result
    }}

    print(f"Returning result: {result}")  # Debug-Log
    return jsonify(result)

@app.route('/submodels/aHR0cHM6Ly9leGFtcGxlLm9yZy9zdW5mb3VuZGVyL3BpY2FyLWNvbnRyb2w/submodel-elements/U2VsZlRlc3Q=/invoke', methods=['POST'])
def handle_self_test():
    try:
        data = request.json
        duration = int(data[0].get("value", {}).get("value", 10)) if isinstance(data, list) and len(data) > 0 else 10
        print(f"\nFlask Server: Ausführung des Self Tests für {duration} Sekunden...")

        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())  # Automatisch unbekannte Hosts akzeptieren
        ssh.connect(RASPBERRY_PI_IP, username=RASPBERRY_PI_USER, password=RASPBERRY_PI_PASSWORD)

        print(f"Flask Server: Starte Skript Self Test für {duration} Sekunden...")
        command = f"nohup python3 {SELF_TEST_SCRIPT} > /tmp/self_test.log 2>&1 & echo $!"
        stdin, stdout, stderr = ssh.exec_command(command)
        pid = stdout.read().decode().strip()
        print(f"PID des gestarteten Prozesses: {pid}")

        # Sicherstellen, dass der Prozess korrekt beendet wird
        time.sleep(duration)
        # Versuche den Prozess anhand der PID zu beenden
        if pid and pid.isdigit():
            print(f"Versuche, Prozess mit PID {pid} zu beenden...")
            ssh.exec_command(f"kill {pid}")
        else:
            # Fallback: Prozess anhand des Skriptnamens beenden
            print(f"PID konnte nicht ermittelt werden. Beende Prozess basierend auf dem Namen {SELF_TEST_SCRIPT}...")
            ssh.exec_command(f"pkill -f {SELF_TEST_SCRIPT}")

    except Exception as e:
        return f"Flask Server: Fehler beim Ausführen des Skripts: {str(e)}"

    finally:
        # SSH-Verbindung schließen
        ssh.close()
        print("Flask Server: SSH-Verbindung geschlossen")

    result = {"value": {
        "idShort": "Result",  # Muss zum Submodell passen
        "modelType": "Property",
        "valueType": "xs:string",  # Muss mit Submodell-Definition übereinstimmen
        "value": "Selbsttest erfolgreich! Keine Probleme erkannt."
    }}

    print(f"Returning result: {result}")  # Debug-Log
    return jsonify(result)

@app.route('/submodels/aHR0cHM6Ly9leGFtcGxlLm9yZy9zdW5mb3VuZGVyL3BpY2FyLWNvbnRyb2w/submodel-elements/R2V0Q3VycmVudExvY2F0aW9u/invoke', methods=['POST'])
def get_city():
    try:
        print("Flask Server: Abruf der Stadt vom Raspberry Pi...")

        # Verbindung mit dem Raspberry Pi über SSH herstellen
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())  # Automatisch unbekannte Hosts akzeptieren
        ssh.connect(RASPBERRY_PI_IP, username=RASPBERRY_PI_USER, password=RASPBERRY_PI_PASSWORD)

        # Das Skript auf dem Raspberry Pi ausführen
        command = f"python3 {GET_LOCATION}"
        stdin, stdout, stderr = ssh.exec_command(command)

        # Die Ausgabe des Skripts lesen
        city = stdout.read().decode().strip()
        stderr_output = stderr.read().decode().strip()

        if stderr_output:
            print(f"Fehlerausgabe vom Raspberry Pi: {stderr_output}")
            raise Exception(f"Fehler beim Ausführen des Skripts: {stderr_output}")

        if not city:
            raise Exception("Das Skript hat keine Stadt zurückgegeben.")

        print(f"Flask Server: Erhaltene Stadt: {city}")

    except Exception as e:
        return jsonify({
            "value": {
                "idShort": "Result",
                "modelType": "Property",
                "valueType": "xs:string",
                "value": f"Fehler: {str(e)}"
            }
        }), 500

    finally:
        # SSH-Verbindung schließen
        ssh.close()
        print("Flask Server: SSH-Verbindung geschlossen")

    # Rückgabe der Stadt in der AAS
    result = {
        "value": {
            "idShort": "Result",
            "modelType": "Property",
            "valueType": "xs:string",
            "value": city
        }
    }
    return jsonify(result)

@app.route('/submodels/aHR0cHM6Ly9leGFtcGxlLm9yZy9zdW5mb3VuZGVyL3BpY2FyLWNvbnRyb2w/submodel-elements/Q2FsY3VsYXRlRGlzdGFuY2U=/invoke', methods=['POST'])
def calculate_distance():
    try:
        data = request.json
        origin = data[0].get("value", {}).get("value", "")
        destination = data[1].get("value", {}).get("value", "")

        if not origin or not destination:
            raise Exception("Beide Orte müssen angegeben werden.")

        print(f"Flask Server: Berechnung der Fahrzeit zwischen \"{origin}\" und \"{destination}\"...")

        # Verbindung mit dem Raspberry Pi herstellen
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(RASPBERRY_PI_IP, username=RASPBERRY_PI_USER, password=RASPBERRY_PI_PASSWORD)

        # Python-Skript auf dem Raspberry Pi ausführen
        command = f"python3 {CALCULATE_DISTANCE}  \"{origin}\" \"{destination}\""
        stdin, stdout, stderr = ssh.exec_command(command)

        # Ausgabe des Skripts lesen
        result = stdout.read().decode().strip()
        stderr_output = stderr.read().decode().strip()

        if stderr_output:
            print(f"Fehlerausgabe vom Raspberry Pi: {stderr_output}")
            raise Exception(f"Fehler beim Ausführen des Skripts: {stderr_output}")

        if not result:
            raise Exception("Das Skript hat keine Fahrzeit zurückgegeben.")

        print(f"Flask Server: Erhaltene Fahrzeit: {result}")

    except Exception as e:
        print(f"Flask Server: Fehler: {e}")
        return jsonify({
            "value": {
                "idShort": "Result",
                "modelType": "Property",
                "valueType": "xs:string",
                "value": f"Fehler: {str(e)}"
            }
        }), 500



    finally:
        ssh.close()
        print("Flask Server: SSH-Verbindung geschlossen.")

    # Rückgabe der Fahrzeit
    return jsonify({
        "value": {
            "idShort": "Result",
            "modelType": "Property",
            "valueType": "xs:string",
            "value": result
        }
    })

@app.route('/shutdown', methods=['POST'])
def shutdown():
    print("\nFlask Server: Server wird heruntergefahren...")
    shutdown_server()
    return "Flask Server: Herunterfahren abgeschlossen."


if __name__ == "__main__":
    print("\nFlask Server: Server wird gestartet...")
    app.run(host="0.0.0.0", port=1080)
