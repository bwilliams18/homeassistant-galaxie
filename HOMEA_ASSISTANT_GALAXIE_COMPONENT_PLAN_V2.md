# Home Assistant Galaxie Component Implementation Plan V2

## Overview
Create a Home Assistant custom component for Galaxie NASCAR analytics platform with proper device organization:
- Separate devices for each series (Cup, Xfinity, Truck) for previous races
- Separate devices for each series for next races  
- Separate devices for each live run when races are active
- Binary sensor for overall live race status

## API Endpoints
- `https://galaxie.app/api/previous_race/` - Returns array of previous races by series
- `https://galaxie.app/api/next_race/` - Returns array of next races by series
- `https://galaxie.app/api/live/` - Returns array of live runs (empty when no race active)

## Device Structure

### 1. Previous Race Devices (3 devices - one per series)
Each device represents the most recent completed race for that series:
- **Device Name**: `Previous Race {Series Name}`
- **Device ID**: `previous_race_{series_name_lower}`
- **Sensors**:
  - Track Name
  - Date (race_date)
  - Scheduled Distance
  - Scheduled Laps
  - Cars In Field
  - Television Broadcaster
  - Radio Broadcaster
  - Playoff Round
  - Winner
  - Actual Distance
  - Actual Laps

### 2. Next Race Devices (3 devices - one per series)
Each device represents the upcoming race for that series:
- **Device Name**: `Next Race {Series Name}`
- **Device ID**: `next_race_{series_name_lower}`
- **Sensors**:
  - Track Name
  - Date (scheduled_date)
  - Scheduled Distance
  - Scheduled Laps
  - Cars In Field
  - Television Broadcaster
  - Radio Broadcaster
  - Playoff Round

### 3. Live Race Devices (Dynamic - one per active run)
Each device represents an active race run:
- **Device Name**: `Live Race {Run Name}`
- **Device ID**: `live_race_{run_id}`
- **Sensors**:
  - Name
  - Type
  - Start Time
  - End Time
  - Total Laps
  - Actual Laps
  - Stage Laps
  - Stage Start
  - Stage Remaining
  - Stage Completed
  - Stage End
  - Track
  - Latitude
  - Longitude
  - Track Type
  - Lap Number
  - Flag
  - Current Stage
  - Laps Remaining
  - Elapsed Time
  - Length

### 4. Live Status Binary Sensor
- **Entity Name**: `Live Race Status`
- **Entity ID**: `binary_sensor.live_race_status`
- **Returns**: `true` if any live races active, `false` otherwise

## Implementation Steps

### Step 1: Update Constants
- Add device info templates for each device type
- Update series mapping
- Add flag mapping
- Define sensor configurations

### Step 2: Update Coordinator
- Ensure proper data structure handling
- Add logging for device creation
- Handle empty live race arrays

### Step 3: Create Device Factory
- Create functions to generate device info for each device type
- Handle dynamic device creation for live races
- Ensure unique device identifiers

### Step 4: Update Sensor Platform
- Create separate sensor classes for each device type
- Implement proper device association
- Handle data extraction for each sensor type
- Add proper availability checks

### Step 5: Update Binary Sensor Platform
- Create single binary sensor for live status
- Implement proper device association
- Handle empty live race arrays

### Step 6: Update Main Integration
- Ensure proper platform setup
- Handle dynamic entity creation
- Add proper cleanup on unload

### Step 7: Testing
- Test with no live races
- Test with active live races
- Verify device grouping
- Check sensor data accuracy

## File Structure
```
custom_components/galaxie/
├── __init__.py
├── manifest.json
├── const.py
├── config_flow.py
├── coordinator.py
├── device.py
├── sensor.py
├── binary_sensor.py
└── translations/
    └── en.json
```

## Expected Results
- **3 Previous Race Devices** (Cup, Xfinity, Truck)
- **3 Next Race Devices** (Cup, Xfinity, Truck)
- **0-N Live Race Devices** (depending on active races)
- **1 Binary Sensor** for overall live status
- **Total Sensors**: ~60-80 sensors across all devices
- **Clean device organization** in Home Assistant UI 