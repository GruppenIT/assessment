# Sistema de Assessment de Cibersegurança

## Overview

This is a Flask-based web application for cybersecurity maturity assessment. The system allows clients to complete cybersecurity assessments while providing administrators with tools to manage domains, questions, and generate reports. Built using the MVC (Model-View-Controller) pattern, the application features user authentication, role-based access control, and comprehensive reporting capabilities.

## System Architecture

### Backend Architecture
- **Framework**: Flask (Python web framework)
- **ORM**: SQLAlchemy with Flask-SQLAlchemy extension
- **Authentication**: Flask-Login for session management
- **Database**: SQLite for development (configurable for PostgreSQL in production)
- **Forms**: WTForms with Flask-WTF for form handling and validation

### Frontend Architecture
- **Template Engine**: Jinja2 (Flask's default templating system)
- **CSS Framework**: Bootstrap 5 for responsive design
- **JavaScript**: Vanilla JavaScript for interactive features
- **Icons**: Font Awesome for iconography

### Design Pattern
- **MVC Pattern**: Clear separation between Models (data), Views (templates), and Controllers (routes)
- **Blueprints**: Modular organization using Flask blueprints for different functional areas

## Key Components

### Models (`/models/`)
- **Usuario**: User management (clients and administrators) with password hashing
- **Dominio**: Cybersecurity domains for organizing questions
- **Pergunta**: Assessment questions linked to domains
- **Resposta**: User responses with 0-5 rating scale and optional comments
- **Logo**: Company logo management for branding

### Routes (`/routes/`)
- **auth**: Authentication (login, registration, logout)
- **admin**: Administrative functions (domain/question management, user oversight)
- **cliente**: Client dashboard and assessment interface
- **relatorio**: Report generation and visualization

### Forms (`/forms/`)
- **auth_forms**: Login and registration forms with validation
- **admin_forms**: Administrative forms for content management
- **assessment_forms**: Assessment response forms with rating system

### Utilities (`/utils/`)
- **auth_utils**: Role-based access control decorators
- **pdf_utils**: PDF report generation using ReportLab
- **upload_utils**: File upload handling with security measures

## Data Flow

### Assessment Process
1. Client logs in and accesses dashboard
2. System displays progress and available domains
3. Client navigates through domains and answers questions
4. Responses are auto-saved with AJAX functionality
5. Progress tracking updates in real-time
6. Assessment completion triggers report generation capability

### Administrative Workflow
1. Admin manages cybersecurity domains and questions
2. System organizes content hierarchically (domains → questions)
3. Admin monitors client progress and completion status
4. Reports are generated on-demand for completed assessments

### Authentication Flow
- Password hashing using Werkzeug security utilities
- Session management through Flask-Login
- Role-based route protection (admin vs. client access)

## External Dependencies

### Core Dependencies
- **Flask**: Web framework foundation
- **SQLAlchemy**: Database ORM and migrations
- **Flask-Login**: User session management
- **WTForms**: Form handling and validation
- **ReportLab**: PDF generation for reports
- **Bootstrap 5**: Frontend CSS framework (CDN)
- **Font Awesome**: Icon library (CDN)

### Security Features
- CSRF protection through Flask-WTF
- Password hashing with Werkzeug
- File upload validation and security
- Role-based access control decorators

## Deployment Strategy

### Development Configuration
- SQLite database for local development
- Debug mode enabled
- Static file serving through Flask
- Environment variables for sensitive configuration

### Production Considerations
- Database migration to PostgreSQL recommended
- Environment-based configuration management
- Static file serving through web server (nginx/Apache)
- WSGI deployment (Gunicorn, uWSGI)
- Proxy configuration with ProxyFix middleware

### File Structure
```
/static/
  /css/ - Custom stylesheets
  /js/ - Client-side JavaScript
  /uploads/ - User-uploaded files (logos)
/templates/ - Jinja2 HTML templates
  /admin/ - Administrative interface templates
  /auth/ - Authentication templates
  /cliente/ - Client interface templates
  /relatorio/ - Report templates
```

## Changelog
- July 07, 2025. Initial setup

## User Preferences

Preferred communication style: Simple, everyday language.