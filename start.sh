#!/bin/bash

# Building Reservation System - Quick Start Script

echo "🏢 Building Reservation System - Quick Start"
echo "=========================================="

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is required but not installed."
    exit 1
fi

# Check if pip is installed
if ! command -v pip3 &> /dev/null && ! command -v pip &> /dev/null; then
    echo "❌ pip is required but not installed."
    exit 1
fi

# Install dependencies
echo "📦 Installing Python dependencies..."
pip install -r requirements.txt

# Check if .env exists, if not copy from example
if [ ! -f .env ]; then
    echo "⚙️  Creating .env file from template..."
    cp .env.example .env
    echo "✅ Created .env file. You can edit it to customize settings."
fi

# Start the application
echo "🚀 Starting the application..."
echo ""
echo "🌐 Access the application at:"
echo "   Client: http://localhost:5000"
echo "   Admin:  http://localhost:5000/admin/login"
echo ""
echo "🔐 Default admin credentials:"
echo "   Username: admin"
echo "   Password: admin123"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

python3 app.py
