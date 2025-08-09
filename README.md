# Home Assistant Galaxie Integration

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://github.com/custom-components/hacs)
[![maintainer](https://img.shields.io/badge/maintainer-%40bwilliams18-blue.svg)](https://github.com/bwilliams18)
[![python_versions](https://img.shields.io/pypi/pyversions/aiohttp.svg)](https://pypi.org/project/aiohttp/)
[![license](https://img.shields.io/github/license/bwilliams18/homeassistant-galaxie.svg)](https://github.com/bwilliams18/homeassistant-galaxie/blob/main/LICENSE)

Home Assistant integration for [Galaxie](https://galaxie.app), a NASCAR analytics platform providing real-time race data, driver statistics, and race analytics.

## 🏁 Features

- **Previous Race Data**: Track information, results, and statistics for completed races
- **Next Race Information**: Upcoming race schedules and details  
- **Live Race Monitoring**: Real-time race data including lap times, positions, and flags
- **Multi-Series Support**: Cup Series, Xfinity Series, and Truck Series
- **Comprehensive Sensors**: 50+ sensors providing detailed race analytics
- **Device Organization**: Clean device grouping for easy navigation

## 📋 Table of Contents

- [Installation](#installation)
- [Configuration](#configuration)
- [Available Sensors](#available-sensors)
- [Development](#development)
- [Contributing](#contributing)
- [Troubleshooting](#troubleshooting)



## 📦 Installation

### HACS (Recommended)

1. **Install HACS** if you haven't already
2. **Add this repository** as a custom repository in HACS:
   - Repository: `bwilliams18/homeassistant-galaxie`
   - Category: Integration
3. **Search for "Galaxie"** in the integrations tab
4. **Click "Download"**
5. **Restart Home Assistant**
6. **Configure**: Settings → Devices & Services → Add Integration → Galaxie

### Manual Installation

1. **Download** the `custom_components/galaxie` folder
2. **Copy** to your Home Assistant `config/custom_components/` directory
3. **Restart** Home Assistant
4. **Configure**: Settings → Devices & Services → Add Integration → Galaxie

## ⚙️ Configuration

1. In Home Assistant, go to **Settings** → **Devices & Services**
2. Click **Add Integration**
3. Search for **Galaxie**
4. Enter a name for the integration
5. Click **Submit**

No additional configuration is required - the integration automatically connects to the Galaxie API.

## 📊 Available Sensors

### Previous Race Sensors (per series)
- **Track Name**: Name of the race track
- **Date**: When the race was held
- **Scheduled Distance**: Planned race distance
- **Scheduled Laps**: Planned number of laps
- **Cars in Field**: Number of cars that started
- **Television Broadcaster**: TV network
- **Radio Broadcaster**: Radio network
- **Playoff Round**: Current playoff round (if applicable)
- **Winner**: Race winner
- **Actual Distance**: Actual race distance completed
- **Actual Laps**: Actual laps completed

### Next Race Sensors (per series)
- **Track Name**: Name of the upcoming track
- **Scheduled Date**: When the race is scheduled
- **Scheduled Distance**: Planned race distance
- **Scheduled Laps**: Planned number of laps
- **Cars in Field**: Expected number of cars
- **Television Broadcaster**: TV network
- **Radio Broadcaster**: Radio network
- **Playoff Round**: Current playoff round (if applicable)

### Live Race Sensors (when active)
- **Race Name**: Name of the current race
- **Type**: Type of race session
- **Start Time**: When the race started
- **End Time**: When the race ended (if applicable)
- **Total Laps**: Total planned laps
- **Actual Laps**: Current lap number
- **Stage Laps**: Laps per stage
- **Current Stage**: Current stage number
- **Laps Remaining**: Laps left in current stage
- **Flag**: Current flag status (Green, Yellow, Red, etc.)
- **Track**: Track name
- **Latitude/Longitude**: Track coordinates
- **Track Type**: Track type (Short track, Road course, etc.)
- **Elapsed Time**: Time since race start
- **Length**: Race length in miles

### Binary Sensors
- **Live Race Status**: `true` if any race is currently active

## 🛠️ Development

For development information, please see [CONTRIBUTING.md](CONTRIBUTING.md).

### Debug Logging

Add this to your Home Assistant `configuration.yaml`:

```yaml
logger:
  default: info
  logs:
    custom_components.galaxie: debug
```

## 🤝 Contributing

Please read [CONTRIBUTING.md](CONTRIBUTING.md) for details on our code of conduct and the process for submitting pull requests.

## 🐛 Troubleshooting

### Common Issues

#### Integration not found
- **Solution**: Restart Home Assistant after installation
- **Check**: Files are in correct directory structure

#### No data showing
- **Solution**: Check internet connection and API status
- **Check**: Home Assistant logs for error messages
- **Verify**: Galaxie API is accessible at https://galaxie.app

#### Sensors not updating
- **Solution**: Check coordinator status in integration settings
- **Note**: Live data updates every 15 seconds, race data every 15 minutes

#### Debug Information
Enable debug logging to see detailed information:

```yaml
logger:
  default: info
  logs:
    custom_components.galaxie: debug
```

### Getting Help

- **GitHub Issues**: [Report bugs or request features](https://github.com/bwilliams18/homeassistant-galaxie/issues)
- **Discussions**: [Community discussions](https://github.com/bwilliams18/homeassistant-galaxie/discussions)
- **Documentation**: [Full documentation](https://github.com/bwilliams18/homeassistant-galaxie/tree/main/docs)

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- [Galaxie](https://galaxie.app) for providing the NASCAR data API
- [Home Assistant](https://home-assistant.io/) for the amazing automation platform
- [HACS](https://hacs.xyz/) for making custom integrations easy to install
- [NASCAR](https://nascar.com) for the racing data

## 📞 Support

- **GitHub Issues**: [Report bugs or request features](https://github.com/bwilliams18/homeassistant-galaxie/issues)
- **Discussions**: [Community discussions](https://github.com/bwilliams18/homeassistant-galaxie/discussions)

---

**Note**: This integration is not affiliated with NASCAR, Galaxie, or Home Assistant. It is an independent community project. 