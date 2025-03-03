# Asset Administration Shell for Autonomous Vehicles

Dieses Repository enthält die Implementierung einer **Asset Administration Shell (AAS) für autonome Fahrzeuge**.  
Als Demonstrator wird das **Sunfounder PiCar-S** verwendet. Die AAS ermöglicht eine strukturierte Verwaltung und Nutzung von Sensordaten mithilfe der **Eclipse BaSyx Plattform**.

## Projektstruktur

- **`main.py`**  
  - Startet den **Flask-Server**  
  - Initialisiert den **opc_ua_consumer**  
  - Startet den **OPC UA Server** auf dem **Raspberry Pi**  

- **`aas_files/`**  
  - Enthält die **Asset Administration Shell (AAS)** im **AASX-Format**  
  - Enthält die **Submodels** als **JSON-Dateien**  

- **`remote_scripts/`**  
  - Beinhaltet alle relevanten Skripte für das **PiCar-S**  

## Hintergrund  

Dieses Projekt ist Teil einer Bachelorarbeit zum Thema **Asset Administration Shell für autonome Fahrzeuge**.  
