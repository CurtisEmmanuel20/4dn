# 4DN Fantasy Football Platform

## Overview
4DN is a fantasy football platform that provides users with player projections and statistics to enhance their fantasy football experience.

## Project Structure
```
4dn-fantasy-football
├── app.py
├── requirements.txt
├── src
│   ├── __init__.py
│   ├── api
│   │   ├── __init__.py
│   │   └── projections.py
│   └── models
│       └── player.py
└── README.md
```

## Setup Instructions

1. **Clone the repository:**
   ```
   git clone <repository-url>
   cd 4dn-fantasy-football
   ```

2. **Create a virtual environment:**
   ```
   python -m venv venv
   ```

3. **Activate the virtual environment:**
   - On Windows:
     ```
     venv\Scripts\activate
     ```
   - On macOS/Linux:
     ```
     source venv/bin/activate
     ```

4. **Install dependencies:**
   ```
   pip install -r requirements.txt
   ```

## Usage

1. **Run the application:**
   ```
   python app.py
   ```

2. **Access the API:**
   - The API can be accessed at `http://localhost:5000/api/projections` to get player projections in JSON format.

## Contributing
Contributions are welcome! Please submit a pull request or open an issue for any suggestions or improvements.