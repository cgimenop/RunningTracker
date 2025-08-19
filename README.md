# RunningTracker
![Tests](https://github.com/cgimenop/RunningTracker/workflows/Tests/badge.svg)
![Coverage](https://github.com/cgimenop/RunningTracker/workflows/Test%20Coverage/badge.svg)


**A comprehensive running data analysis and visualization platform**

RunningTracker is a Python-based application that parses TCX (Training Center XML) files from GPS running devices, stores the data in MongoDB, and provides a web-based dashboard for analyzing running performance. Track your progress, analyze lap times, visualize routes, and monitor your running statistics over time.

## Features

- **TCX File Processing**: Parse Garmin and other GPS device files
- **Data Storage**: MongoDB integration for persistent data storage
- **Excel Export**: Generate detailed Excel reports with lap summaries
- **Web Dashboard**: Interactive charts and performance analytics
- **Performance Tracking**: Monitor fastest/slowest laps, distances, and times
- **Docker Support**: Easy deployment with containerization

## Quick Start

### Prerequisites

- Python 3.11+
- MongoDB (local or Docker)
- Docker & Docker Compose (for containerized deployment)

## Installation & Usage

### Option 1: Docker Compose (Recommended)

1. **Clone and navigate to the repository**:
   ```bash
   git clone <repository-url>
   cd RunningTracker
   ```

2. **Start all services**:
   ```bash
   # Development mode (with debug enabled)
   docker-compose up

   # Production mode
   FLASK_ENV=production docker-compose up
   ```

3. **Access the web dashboard**:
   - Open http://localhost:5050 in your browser

4. **Process TCX files**:
   - Place your .tcx files in the `./data` directory
   - The trainparser service will automatically process them

### Option 2: Local Development

1. **Set up Python environment**:
   ```bash
   # Create and activate virtual environment
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate

   # Install dependencies
   pip install -r requirements.txt
   ```

2. **Start MongoDB** (if not using Docker):
   ```bash
   # Using Homebrew on macOS
   brew services start mongodb-community

   # Or using Docker
   docker run -d -p 27017:27017 --name mongodb mongo:6.0
   ```

3. **Process TCX files**:
   ```bash
   # Parse single file
   python src/trainparser.py data/your-file.tcx --mongo

   # Parse entire directory
   python src/trainparser.py data/ --mongo

   # Export to Excel only
   python src/trainparser.py data/ --output results.xlsx
   ```

4. **Start web application**:
   ```bash
   cd webapp

   # Development mode
   FLASK_ENV=development python app.py

   # Production mode
   FLASK_ENV=production python app.py
   ```

5. **Access the dashboard**:
   - Open http://localhost:5000 in your browser

### Option 3: Manual Setup

1. **Install MongoDB**:
   ```bash
   # macOS
   brew install mongodb-community

   # Ubuntu/Debian
   sudo apt-get install mongodb

   # Or use Docker
   docker run -d -p 27017:27017 mongo:6.0
   ```

2. **Install Python dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Run components separately**:
   ```bash
   # Process TCX files
   python src/trainparser.py data/ --mongo

   # Start web server
   cd webapp && python app.py
   ```

## Configuration

### Environment Variables

- `FLASK_ENV`: Set to `development` or `production`
- `MONGO_URI`: MongoDB connection string (default: `mongodb://localhost:27017`)

### File Structure

```
RunningTracker/
├── src/
│   ├── trainparser.py      # TCX file processor
│   └── test/
├── webapp/
│   ├── app.py             # Flask web application
│   ├── config/            # Environment configurations
│   ├── static/            # CSS, JS, images
│   └── templates/         # HTML templates
├── data/                  # Place your .tcx files here
├── output/               # Excel exports
├── docker-compose.yml    # Docker services
└── requirements.txt      # Python dependencies
```

## Usage Examples

### Command Line Options

```bash
# Basic usage
python src/trainparser.py data/run.tcx

# Export modes
python src/trainparser.py data/ --mode summary    # Lap summaries only
python src/trainparser.py data/ --mode detailed   # Detailed trackpoints
python src/trainparser.py data/ --mode both       # Both (default)

# MongoDB integration
python src/trainparser.py data/ --mongo --mongo-uri mongodb://localhost:27017

# Custom output
python src/trainparser.py data/ --output my-results.xlsx
```

### Web Dashboard Features

- **Performance Charts**: Visualize lap times and distances
- **Records Tracking**: View fastest/slowest laps and longest runs
- **Data Tables**: Detailed lap-by-lap analysis
- **Date Filtering**: Analyze performance over time

## Development

### Running Tests

```bash
python -m pytest src/test/
```

### Environment Setup Script

```bash
# Quick environment setup
./env.sh
```

## Troubleshooting

### Common Issues

1. **MongoDB Connection Error**:
   - Ensure MongoDB is running
   - Check connection string in configuration

2. **TCX File Not Parsing**:
   - Verify file format is valid TCX
   - Check file permissions

3. **Web Dashboard Not Loading**:
   - Confirm Flask app is running
   - Check MongoDB has data

### Docker Issues

```bash
# Rebuild containers
docker-compose down && docker-compose up --build

# View logs
docker-compose logs webapp
docker-compose logs trainparser
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

This project is for personal use. Please respect the terms of any third-party libraries used.
