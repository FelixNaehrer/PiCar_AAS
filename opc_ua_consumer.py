from opcua import Client
import time
import requests
from datetime import datetime
import threading

# Verbindung zu den beiden OPC UA Servern herstellen
sensor_url = "opc.tcp://172.20.10.2:4840/freeopcua/sensor/"
heartbeat_url = "opc.tcp://172.20.10.2:4841/freeopcua/heartbeat/"

sensor_client = Client(sensor_url)
heartbeat_client = Client(heartbeat_url)

# Ziel-URL für den POST-Request
post_url_sensor_data = "http://localhost:8081/submodels/aHR0cHM6Ly9hZG1pbi1zaGVsbC5pby9pZHRhL1N1Ym1vZGVsVGVtcGxhdGUvVGltZVNlcmllcy8xLzE/submodel-elements/Segments.InternalSegment.Records"
put_url_serial_number = "http://localhost:8081/submodels/aHR0cHM6Ly9hZG1pbi1zaGVsbC5pby9pZHRhL1N1Ym1vZGVsVGVtcGxhdGUvRGlnaXRhbE5hbWVwbGF0ZS8yLzA/submodel-elements/SerialNumber?level=deep"
put_url_usb_port = "http://localhost:8081/submodels/aHR0cHM6Ly9hZG1pbi1zaGVsbC5pby9aVkVJL1RlY2huaWNhbERhdGEvU3VibW9kZWwvMS8y/submodel-elements/TechnicalProperties.USBPortKonfiguration?level=deep"
headers = {"Content-Type": "application/json"}

def fetch_sensor_data():
    """Sensor-Daten aus dem OPC UA Sensor-Server abrufen."""
    data = {
        "memory_usage": sensor_client.get_node("ns=2;s=memory_usage").get_value(),
        "available_memory": sensor_client.get_node("ns=2;s=available_memory").get_value(),
        "cpu_usage": sensor_client.get_node("ns=2;s=cpu_usage").get_value(),
        "cpu_temperature": sensor_client.get_node("ns=2;s=cpu_temperature").get_value(),
        "ultrasonic_distance": sensor_client.get_node("ns=2;s=ultrasonic_distance").get_value(),
        "line_follower_digital": [
            sensor_client.get_node(f"ns=2;s=line_follower_digital_{i}").get_value() for i in range(5)
        ],
        "light_sensor": [
            sensor_client.get_node(f"ns=2;s=light_sensor_a{i}").get_value() for i in range(3)
        ],
    }
    # Sensor-Daten in der Konsole ausgeben
    print("=" * 80)
    print("SENSOR-DATEN:")
    print(f"Memory Usage: {data['memory_usage']:.2f}%")
    print(f"Available Memory: {data['available_memory']:.2f} MB")
    print(f"CPU Usage: {data['cpu_usage']:.2f}%")
    print(f"CPU Temperature: {data['cpu_temperature']:.2f}°C")
    print(f"Ultrasonic Distance: {data['ultrasonic_distance']:.2f} cm")
    print("Line Follower Digital:", ", ".join(map(str, data["line_follower_digital"])))
    print("Light Sensor:", ", ".join(map(str, data["light_sensor"])))
    print("=" * 80)
    return data

def fetch_heartbeat_data():
    """Fetch heartbeat data from the OPC UA Heartbeat server, including USB port data."""
    data = {
        "disk_total": heartbeat_client.get_node("ns=2;s=disk_total").get_value(),
        "disk_used": heartbeat_client.get_node("ns=2;s=disk_used").get_value(),
        "disk_free": heartbeat_client.get_node("ns=2;s=disk_free").get_value(),
        "network_sent": heartbeat_client.get_node("ns=2;s=network_sent").get_value(),
        "network_received": heartbeat_client.get_node("ns=2;s=network_received").get_value(),
        "uptime": heartbeat_client.get_node("ns=2;s=uptime").get_value(),
        "serial_number": heartbeat_client.get_node("ns=2;s=serial_number").get_value(),
        "usb_ports": [
            heartbeat_client.get_node(f"ns=2;s=usb_port_{i+1}").get_value()
            for i in range(4)
        ]
    }

    # Print heartbeat data in the console
    print("=" * 80)
    print("HEARTBEAT DATA:")
    print(f"Disk Total: {data['disk_total']:.2f} GB")
    print(f"Disk Used: {data['disk_used']:.2f} GB")
    print(f"Disk Free: {data['disk_free']:.2f} GB")
    print(f"Network Sent: {data['network_sent']:.2f} MB")
    print(f"Network Received: {data['network_received']:.2f} MB")
    print(f"Uptime: {data['uptime']}")
    print(f"Serial Number: {data['serial_number']}")
    print("-" * 80)
    print("USB PORT DATA:")
    for i, port_data in enumerate(data['usb_ports']):
        print(f"USB Port {i+1}: {port_data}")
    print("=" * 80)

    return data


def send_sensor_data_to_aas(sensor_data):
    """Sensor-Daten an die AAS senden."""
    timestamp = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
    data = {
        "idShort": f"Record{timestamp}",
        "modelType": "SubmodelElementCollection",
        "value": [
            {"idShort": "Time", "modelType": "Property", "valueType": "xs:dateTime", "value": timestamp},
            {"idShort": "MemoryUsage", "modelType": "Property", "valueType": "xs:float", "value": sensor_data["memory_usage"]},
            {"idShort": "AvailableMemory", "modelType": "Property", "valueType": "xs:float", "value": sensor_data["available_memory"]},
            {"idShort": "CPUUsage", "modelType": "Property", "valueType": "xs:float", "value": sensor_data["cpu_usage"]},
            {"idShort": "Temperature", "modelType": "Property", "valueType": "xs:float", "value": sensor_data["cpu_temperature"]},
            {"idShort": "UltrasonicDistance", "modelType": "Property", "valueType": "xs:float", "value": sensor_data["ultrasonic_distance"]},
            *[
                {"idShort": f"LineFollowerDigital{i}", "modelType": "Property", "valueType": "xs:int", "value": v}
                for i, v in enumerate(sensor_data["line_follower_digital"])
            ],
            *[
                {"idShort": f"LightSensorA{i}", "modelType": "Property", "valueType": "xs:int", "value": v}
                for i, v in enumerate(sensor_data["light_sensor"])
            ],
        ],
    }
    try:
        response = requests.post(post_url_sensor_data, headers=headers, json=data)
        if response.status_code == 201:
            print("Sensor-Daten erfolgreich gesendet")
        else:
            print(f"Fehler beim Senden: {response.status_code} - {response.text}")
    except requests.RequestException as e:
        print(f"HTTP-Fehler: {e}")


def send_heartbeat_data_to_aas(heartbeat_data):
    """Heartbeat-Daten an die AAS senden."""
    """Update Serial Number"""
    data = {
        "modelType": "Property",
        "semanticId": {
            "keys": [
                {
                    "type": "GlobalReference",
                    "value": "0173-1#02-AAM556#002"
                }
            ],
            "type": "ExternalReference"
        },
        "value": heartbeat_data['serial_number'],
        "valueType": "xs:string",
        "qualifiers": [
            {
                "kind": "ConceptQualifier",
                "type": "Multiplicity",
                "value": "ZeroToOne",
                "valueType": "xs:string"
            }
        ],
        "description": [
            {
                "language": "en",
                "text": "Note: see also [IRDI] 0112/2///61987#ABA951#007 serial number "
            }
        ],
        "idShort": "SerialNumber"
    }
    try:
        response = requests.put(put_url_serial_number, headers=headers, json=data)
        if response.status_code == 204:
            print("Serial Number erfolgreich gesendet")
        else:
            print(f"Fehler beim Senden der Serial Number: {response.status_code} - {response.text}")
    except requests.RequestException as e:
        print(f"HTTP-Fehler: {e}")

    """Update USB Ports Number"""
    data = {
        "modelType": "SubmodelElementCollection",
        "idShort": "USBPortKonfiguration",
        "value": [
            {
                "modelType": "Property",
                "value": heartbeat_data['usb_ports'][0],
                "valueType": "xs:string",
                "description": [
                    {
                        "language": "en",
                        "text": "Details of the device connected to USB Port 1."
                    }
                ],
                "idShort": "USBPort1"
            },
            {
                "modelType": "Property",
                "value": heartbeat_data['usb_ports'][1],
                "valueType": "xs:string",
                "description": [
                    {
                        "language": "en",
                        "text": "Details of the device connected to USB Port 2."
                    }
                ],
                "idShort": "USBPort2"
            },
            {
                "modelType": "Property",
                "value": heartbeat_data['usb_ports'][2],
                "valueType": "xs:string",
                "description": [
                    {
                        "language": "en",
                        "text": "Details of the device connected to USB Port 3."
                    }
                ],
                "idShort": "USBPort3"
            },
            {
                "modelType": "Property",
                "value": heartbeat_data['usb_ports'][3],
                "valueType": "xs:string",
                "description": [
                    {
                        "language": "en",
                        "text": "Details of the device connected to USB Port 4."
                    }
                ],
                "idShort": "USBPort4"
            }
        ]
    }
    try:
        response = requests.put(put_url_usb_port, headers=headers, json=data)
        if response.status_code == 204:
            print("USB Ports erfolgreich gesendet")
        else:
            print(f"Fehler beim Senden der USB Ports: {response.status_code} - {response.text}")
    except requests.RequestException as e:
        print(f"HTTP-Fehler: {e}")


def start_opcua_consumer():
    """Startet den OPC UA Consumer."""
    try:
        sensor_client.connect()
        heartbeat_client.connect()
        print("OPC-UA-Consumer: Verbunden mit beiden OPC UA Servern.")

        sensor_counter = 0
        heartbeat_counter = 0

        while True:
            # Sensor-Daten alle 10 Sekunden abrufen und senden
            if sensor_counter >= 10:
                sensor_data = fetch_sensor_data()
                send_sensor_data_to_aas(sensor_data)
                sensor_counter = 0

            # Heartbeat-Daten jede Minute abrufen und senden
            if heartbeat_counter >= 60:
                heartbeat_data = fetch_heartbeat_data()
                send_heartbeat_data_to_aas(heartbeat_data)
                heartbeat_counter = 0

            sensor_counter += 1
            heartbeat_counter += 1
            time.sleep(1)

    except KeyboardInterrupt:
        print("\nOPC-UA-Consumer: Überwachung beendet.")

    finally:
        sensor_client.disconnect()
        heartbeat_client.disconnect()
        print("OPC-UA-Consumer: Verbindung zu beiden Servern beendet.")


class OpcUaThread(threading.Thread):
    """Thread-Klasse für den OPC UA Consumer."""
    def run(self):
        start_opcua_consumer()
