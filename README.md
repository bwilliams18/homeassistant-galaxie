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

- [Repository Setup](#repository-setup)
- [How It Works](#how-it-works)
- [Installation](#installation)
- [Configuration](#configuration)
- [Available Sensors](#available-sensors)
- [Development](#development)
- [Contributing](#contributing)
- [Troubleshooting](#troubleshooting)

## 🚀 Repository Setup

### Prerequisites

- Git installed on your system
- GitHub account
- Python 3.9+ (for development)
- Home Assistant instance (for testing)

### Step 1: Create GitHub Repository

1. **Go to GitHub.com** and sign in
2. **Click "New repository"** (green button)
3. **Repository settings:**
   - **Name**: `homeassistant-galaxie`
   - **Description**: `Home Assistant integration for Galaxie NASCAR analytics platform`
   - **Visibility**: Public
   - **Initialize with**: 
     - ✅ README
     - ✅ .gitignore (Python)
     - ✅ License (MIT)
4. **Click "Create repository"**

### Step 2: Clone and Setup Local Repository

```bash
# Clone the repository
git clone https://github.com/YOUR_USERNAME/homeassistant-galaxie.git
cd homeassistant-galaxie

# Set up development environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install development dependencies
pip install aiohttp pytest black isort
```

### Step 3: Copy Integration Files

```bash
# Create the component directory structure
mkdir -p custom_components/galaxie

# Copy all integration files from the main project
cp -r /path/to/main/project/homeassistant-galaxie/custom_components/galaxie/* custom_components/galaxie/
```

### Step 4: Initial Git Setup

```bash
# Add all files to Git
git add .

# Create initial commit
git commit -m "Initial commit: Home Assistant Galaxie integration"

# Push to GitHub
git push -u origin main
```

## 🔧 How It Works

### Repository Structure

```
homeassistant-galaxie/
├── .github/                    # GitHub Actions workflows
│   └── workflows/
│       ├── ci.yml             # Continuous Integration
│       └── hacs-validation.yml # HACS validation
├── custom_components/          # Home Assistant custom components
│   └── galaxie/               # Galaxie integration
│       ├── __init__.py        # Main integration entry point
│       ├── manifest.json      # Integration metadata
│       ├── const.py           # Constants and configuration
│       ├── config_flow.py     # Configuration flow
│       ├── coordinator.py     # Data coordinator
│       ├── device.py          # Device information
│       ├── sensor.py          # Sensor entities
│       ├── binary_sensor.py   # Binary sensor entities
│       ├── logo.png           # Integration icon
│       └── translations/      # Localization
│           └── en.json
├── docs/                      # Documentation
│   ├── installation.md
│   ├── configuration.md
│   └── troubleshooting.md
├── tests/                     # Test suite
│   ├── test_config_flow.py
│   ├── test_coordinator.py
│   └── test_sensors.py
├── .gitignore                 # Git ignore rules
├── LICENSE                    # MIT License
├── README.md                  # This file
└── requirements.txt           # Python dependencies
```

### Integration Architecture

#### 1. **Data Flow**
```
Galaxie API → Coordinator → Sensors → Home Assistant UI
```

- **API Endpoints**: Fetches data from Galaxie's REST API
- **Coordinator**: Manages data fetching, caching, and updates
- **Sensors**: Extract specific data points from API responses
- **UI**: Displays data in Home Assistant interface

#### 2. **Device Organization**
```
Galaxie Integration
├── Previous Race NASCAR Cup Series
│   ├── Track Name
│   ├── Date
│   ├── Distance
│   └── ...
├── Next Race NASCAR Cup Series
│   ├── Track Name
│   ├── Scheduled Date
│   └── ...
├── Live Race Status (Binary Sensor)
└── Live Race Devices (when active)
    ├── Race Name
    ├── Lap Number
    ├── Flag Status
    └── ...
```

#### 3. **Update Intervals**
- **Live Race Data**: Updates every 15 seconds
- **Previous/Next Race Data**: Updates every 15 minutes
- **Error Handling**: Graceful fallback to empty data on API failures

### Git Workflow

#### **Branch Strategy**
```
main (production)
├── develop (development)
├── feature/new-sensor
├── bugfix/fix-api-call
└── hotfix/critical-bug
```

#### **Development Workflow**
1. **Create feature branch**: `git checkout -b feature/new-sensor`
2. **Make changes**: Edit files, add tests
3. **Commit changes**: `git commit -m "Add new sensor for lap times"`
4. **Push branch**: `git push origin feature/new-sensor`
5. **Create Pull Request**: On GitHub
6. **Code review**: Get feedback and make changes
7. **Merge**: Merge to `develop` branch
8. **Release**: Merge `develop` to `main` for releases

#### **Version Management**
- **Semantic Versioning**: `MAJOR.MINOR.PATCH`
- **Changelog**: Document all changes
- **Git Tags**: Tag releases for easy reference

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

### Local Development Setup

```bash
# Clone the repository
git clone https://github.com/YOUR_USERNAME/homeassistant-galaxie.git
cd homeassistant-galaxie

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Install development tools
pip install black isort pytest pytest-cov
```

### Testing

```bash
# Run all tests
pytest tests/

# Run with coverage
pytest --cov=custom_components.galaxie tests/

# Run specific test file
pytest tests/test_sensors.py

# Run with verbose output
pytest -v tests/
```

### Code Quality

```bash
# Format code with Black
black custom_components/

# Sort imports with isort
isort custom_components/

# Check for issues
flake8 custom_components/
```

### Testing in Home Assistant

1. **Copy integration** to your Home Assistant `config/custom_components/` directory
2. **Restart** Home Assistant
3. **Configure** the integration
4. **Check logs** for any errors
5. **Test sensors** and functionality

### Debug Logging

Add this to your Home Assistant `configuration.yaml`:

```yaml
logger:
  default: info
  logs:
    custom_components.galaxie: debug
```

## 🤝 Contributing

### How to Contribute

1. **Fork** the repository
2. **Create** a feature branch: `git checkout -b feature/amazing-feature`
3. **Make** your changes
4. **Add tests** for new functionality
5. **Run tests** to ensure everything works
6. **Commit** your changes: `git commit -m 'Add amazing feature'`
7. **Push** to your branch: `git push origin feature/amazing-feature`
8. **Create** a Pull Request

### Development Guidelines

- **Follow PEP 8** for Python code style
- **Use Black** for code formatting
- **Write tests** for new functionality
- **Update documentation** when adding features
- **Use descriptive commit messages**

### Pull Request Process

1. **Update documentation** if needed
2. **Add tests** for new functionality
3. **Ensure all tests pass**
4. **Update version** in `manifest.json`
5. **Update changelog** if needed
6. **Request review** from maintainers

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
- **Documentation**: [Full documentation](https://github.com/bwilliams18/homeassistant-galaxie/tree/main/docs)

---

**Note**: This integration is not affiliated with NASCAR, Galaxie, or Home Assistant. It is an independent community project.

## 🔄 Git Workflow Summary

### Daily Development
```bash
# Start work
git checkout develop
git pull origin develop
git checkout -b feature/your-feature

# Make changes and commit
git add .
git commit -m "Add feature description"

# Push and create PR
git push origin feature/your-feature
# Create Pull Request on GitHub
```

### Release Process
```bash
# Merge develop to main
git checkout main
git merge develop
git tag v1.0.0
git push origin main --tags

# Create GitHub release
# Go to GitHub → Releases → Create new release
```

### Hotfix Process
```bash
# Create hotfix branch from main
git checkout main
git checkout -b hotfix/critical-bug
# Fix the bug
git commit -m "Fix critical bug"
git push origin hotfix/critical-bug
# Create PR to main
```

This workflow ensures clean, organized development with proper version control and release management. 