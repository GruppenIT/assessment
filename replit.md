# Sistema de Avaliações de Maturidade

## Overview

This Flask-based web application provides a comprehensive system for multi-type maturity assessments (e.g., cybersecurity, compliance). It enables administrators to manage various assessment types, register clients with multiple respondents, and conduct detailed assessments. Key features include multi-level authentication, role-based access control, CSV bulk import for content, and robust reporting capabilities with AI-driven insights and formal PDF generation. The system is designed following the MVC pattern to ensure modularity and scalability.

## User Preferences

Preferred communication style: Simple, everyday language.

## System Architecture

### Backend
- **Framework**: Flask (Python)
- **ORM**: SQLAlchemy with Flask-SQLAlchemy
- **Authentication**: Flask-Login
- **Database**: PostgreSQL (production), SQLite (development)
- **Forms**: WTForms with Flask-WTF
- **Design Pattern**: MVC (Model-View-Controller) with Flask Blueprints for modularity.

### Frontend
- **Template Engine**: Jinja2
- **CSS Framework**: Bootstrap 5 for responsive design
- **JavaScript**: Vanilla JavaScript for interactivity, SortableJS for drag-and-drop.
- **Icons**: Font Awesome

### Core Features
- **Models**: `Usuario` (admins), `TipoAssessment` (assessment types), `Cliente`, `Respondente`, `Dominio`, `Pergunta`, `Resposta`, `ClienteAssessment`, `Logo`. Includes comprehensive assessment versioning with `AssessmentTipo`, `AssessmentVersao`, `AssessmentDominio` for managing draft/published/archived states.
- **Routes**: Modularized for `auth`, `admin`, `respondente`, `cliente`, `relatorio`.
- **Forms**: Dedicated forms for authentication, administration, client management, and assessment responses.
- **Utilities**:
    - `auth_utils`: Role-based access control.
    - `pdf_utils`: Formal PDF report generation using ReportLab, including AI-generated sections and detailed analysis with preserved line breaks.
    - `upload_utils`: Secure file handling for logos.
    - `csv_utils`: Bulk import for domains and questions, supporting assessment versioning.
    - `openai_monitor`: Monitors OpenAI payload for size, token estimation, and performance.
- **Assessment Process**: Clients respond to questions with a 0-5 rating, progress is tracked, and auto-saved with AJAX.
- **Administrative Workflow**: Admins manage assessment content, monitor client progress, and generate reports.
- **Authentication**: Password hashing with Werkzeug, Flask-Login for sessions, role-based access.
- **UI/UX**: Responsive design with Bootstrap, intuitive drag-and-drop for question reordering, comprehensive admin dashboard with statistics and activity tracking, "Aguarde..." loading interface for OpenAI processes. Professional PDF report styling.
- **Project Configuration**: Projects are associated with specific assessment versions, and evaluators can be assigned.
- **AI Integration**: Uses OpenAI for generating report introductions and final considerations, with payload optimization and a loading interface.
- **On-Premise Deployment**: Designed for robust on-premise deployment, including an `env_loader.py` for environment variable management and comprehensive installation/update scripts.
- **Supervisor Configuration Fix**: Resolved production deployment issue where Supervisor couldn't parse complex environment variables with special characters by implementing .env file approach.
- **Database URL Encoding Fix**: Resolved PostgreSQL connection error by properly URL-encoding special characters (@→%40, !→%21) in database password for production deployment.
- **Unified Deployment Script**: Created `deploy_onpremise_unified.sh` - comprehensive deployment script that preserves all existing data (projects, clients, users, assessments) while updating code from Git. Includes automatic security fixes, database structure verification, complete backup system, and automatic bug fixes for known issues (auth profile, form validation, template corrections).
- **Profile Page Corrections**: Fixed 'hasattr' undefined error by replacing with getattr and Jinja2 'is defined' checks. Implemented complete password change functionality with validation, audit logging, and error handling. Created `aplicar_correcao_perfil.sh` for quick deployment of profile fixes.

## External Dependencies

- **Flask**: Main web framework.
- **SQLAlchemy**: ORM for database interactions.
- **Flask-Login**: User session management.
- **WTForms**: Form rendering and validation.
- **ReportLab**: PDF generation library.
- **Bootstrap 5**: Frontend CSS framework (CDN).
- **Font Awesome**: Icon library (CDN).
- **OpenAI API**: For AI-driven text generation.
- **Pytz**: For timezone handling in dashboards.
- **SortableJS**: For drag-and-drop functionality.