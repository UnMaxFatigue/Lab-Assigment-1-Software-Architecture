# SmartMove System — Requirements 

# Requirements

## Functional Requirements

### General

- **Fr-1.1:** The system shall be composed of one centralized backend system, a
multitude of individual vehicle subsystems, and a multitude of "rental app"
subsystems.

- **Fr-1.2:** The backend system shall be indivisible and monolithic.

- **Fr-1.3:** The type of vehicles in the system shall be: Bicycles, Electric Scooters, and Mopeds

- **Fr-1.4:** The rental app shall be available in the following cities: London,
Milan, and Rome.

### Vehicle State Management

- **Fr-2.1:** An individual vehicle subsystem shall be composed of at least the
following states: Available, Reserved, InUse, Maintenance, EmergencyLock, and
Relocating.

- **Fr-2.2:**: The backend subsystem shall have the exclusive responsibility of
managing the following states of all vehicle subsystems: Available, Reserved,
InUse, Maintenance, EmergencyLock, and Relocating.

- **Fr-2.3:** The maintenance state shall be entered when either the vehicle
encounters a fault or its battery is low.

- **Fr-2.4:** The EmergencyLock state shall be entered when the vehicle is moved
without an active rental or if the vehicle is critically overheated.


### Multi-Tenant Regulatory Logic

- **Fr-3.1:** The backend subsystem shall identify the vehicle's location and
obey local constraints if applicable. 

- **Fr-3.2:** The backend subsystem shall apply a mandatory "Congestion Charge"
to the final bill for all rentals in London.

- **Fr-3.3:** The backend subsystem shall perform a "Helmet Presence Check" and
prevent Moped unlocking if the check fails in Milan.

- **Fr-3.4:** The backend subsystem shall monitor restrict scooters from entering prohibited "Zones" in Rome.

### Telemetry Processing and Hardware Intervention

- **Fr-4.1:** The backed subsystems shall at least collect the following 
telemetry data from the vehicle fleet: GPS coordinates, battery percentage, and
component temperature.

- **Fr-4.2:** The final representation of telemetry data shall be eventually consistent.
The order and timing of the arrival of telemetry messages shall not affect the final representation of the vehicle.

- **Fr-4.3:** The backend subsystems shall intervene in the event of the following scenarios:
The vehicles report a temperature in excess of 60 degrees centigrade or reports 
a battery level bellow 5 percentage points during an active trip.
The backend system shall respond by either ordering the vehicle to slow down or
initiating an emergency termination of the rental.

### Integrity, Persistence, and the Audit Trail

- **Fr-5.1:** The system shall log the following information: When a vehicle
change state or when a payment is processed.

- **Fr-5.2:** The log shall be persist between the system backends sessions.

- **Fr-5.3:** The log shall be accessible for administrator even in the event
that the backend system is not running.

## Quality Attribute Requirements

### Performance

- **QAR-1.1:** The backend subsystem must be able to handle at least thosends of
vehicles.

### Availability? Safety?

- **QAR-2.1:** To detect corruption and tampering the system shall include a
sequential ID for each entry in the log.

- **QAR-2.2:** To detect corruption and tampering the system shall include a
checksum mechanism for each entry in the log.

- **QAR-2.3:** In the event that writing an event to the persist log fails then
the system shall roll back there in memory data representation so that it
matches the log. 

## Implementation Constraints

- **IC-1:** The vehicle subsystem states: Available, Reserved, InUse,
Maintenance, EmergencyLock, and Relocating shall be implemented with a state
machine.

- **IC-2:** All writing of persist data must be done in local CSV or JSON files.
