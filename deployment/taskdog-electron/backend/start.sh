#!/bin/bash
# Test script for TaskDog backend

echo "Installing dependencies..."
pip3 install -r requirements.txt

echo "Starting TaskDog backend server..."
python3 app.py