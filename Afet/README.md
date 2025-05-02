# Afet - Disaster Communication System

Automatic WhatsApp Status Tracking System for Emergency Situations.

## Overview

This system automatically tracks the safety status of employees during disaster situations (earthquakes, floods, fires, etc.) via WhatsApp. The system sends automated messages to employees, processes their responses, and takes appropriate actions based on their status.

## Features

- **Automated Messaging**: Sends WhatsApp messages to employees during emergencies
- **Response Processing**: Categorizes responses into different status types
- **Admin Dashboard**: Real-time monitoring of employee statuses
- **Support Request Handling**: Special handling for "Destek" (Support) requests
- **Logging**: Records all communications for compliance and auditing

## Setup

1. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

2. Configure environment variables:
   - Copy `.env.example` to `.env`
   - Fill in your WhatsApp Business API credentials and database connection details

3. Run the application:
   ```
   python app.py
   ```

4. Access the admin dashboard at http://localhost:5000/admin

## Technologies Used

- **Backend**: Flask
- **Database**: MongoDB
- **Messaging**: WhatsApp Business API
- **Frontend**: HTML, CSS, JavaScript

## Project Structure

- `/app`: Main application code
  - `/api`: API endpoints
  - `/models`: Data models
  - `/services`: Business logic
  - `/templates`: Frontend templates
  - `/static`: Static assets
- `/config`: Configuration files
- `/tests`: Test code

## WhatsApp Message Templates

The system uses predefined message templates:
1. Initial status inquiry
2. Status confirmation responses
3. Support routing messages 