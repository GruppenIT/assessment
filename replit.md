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
- **Models**: `Usuario` (admins), `TipoAssessment` (assessment types), `Cliente`, `Respondente`, `Dominio`, `Pergunta`, `Resposta`, `ClienteAssessment`, `Logo`, `AssessmentPublico`, `RespostaPublica`. Includes comprehensive assessment versioning with `AssessmentTipo`, `AssessmentVersao`, `AssessmentDominio` for managing draft/published/archived states.
- **Routes**: Modularized for `auth`, `admin`, `respondente`, `cliente`, `relatorio`, `publico`.
- **Forms**: Dedicated forms for authentication, administration, client management, and assessment responses. Includes public assessment forms for anonymous responses and lead capture.
- **Utilities**:
    - `auth_utils`: Role-based access control.
    - `pdf_utils`: Formal PDF report generation using ReportLab, including AI-generated sections and detailed analysis with preserved line breaks.
    - `upload_utils`: Secure file handling for logos.
    - `csv_utils`: Bulk import for domains and questions, supporting assessment versioning.
    - `openai_monitor`: Monitors OpenAI payload for size, token estimation, and performance.
    - `publico_utils`: Calculate scores and generate AI recommendations for public assessments.
    - `email_utils`: SMTP email sending with OAuth2 Microsoft 365 and basic authentication support, lead notification system.
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
- **Public Assessment Deployment Script**: Created `deploy_onpremise_com_publico.sh` - enhanced deployment script that includes all protections from the unified script PLUS automatic application of public assessment migrations (new tables, columns, indexes). Features idempotent SQL migrations that can run multiple times safely, automatic rollback on errors, and comprehensive verification. Documented in `DEPLOY_PUBLICO_README.md`.
- **Profile Page Corrections**: Fixed 'hasattr' undefined error by replacing with getattr and Jinja2 'is defined' checks. Implemented complete password change functionality with validation, audit logging, and error handling. Created `aplicar_correcao_perfil.sh` for quick deployment of profile fixes.
- **Password Encoding Security**: Fixed login issues with special characters (@, #, !, etc.) by implementing `utils/password_utils.py` with UTF-8 normalization and robust password verification. Created `aplicar_correcao_senha_especial.sh` for deployment.
- **Two-Factor Authentication (2FA)**: Complete TOTP implementation with QR code setup, backup codes, user self-reset, and admin reset capabilities. Mandatory for respondents, optional for admins. Includes comprehensive audit trail and session management.
- **Mandatory Password Change**: Administrators can force respondents to change passwords on next login via checkbox in respondent editing. After login and 2FA verification, users are redirected to mandatory password change page. Flag is automatically cleared after successful password update.
- **Public Assessment URL System**: Shareable URLs for assessments marked as "URL Pública". Anonymous users can respond to simplified questions (3 options: Não=0, Parcial=3, Sim=5), provide contact information (lead capture), and receive AI-generated domain-specific recommendations. Mobile-first design with progress tracking, one domain per page navigation, and secure token-based access to results. Respondent data is collected after answering questions to avoid integrity errors.
- **Corporate Branding**: Four company logos (Gruppen, Zerobox, Firewall365, GSecDo) displayed in a black banner across public assessment pages (responder_dominio.html, resultado.html) and PDF reports. Dark theme applied to public assessment interface with gradient backgrounds (#1a1a2e to #16213e) for modern, professional appearance. Logo paths use Flask's current_app.root_path for deployment portability.
- **Email Notification System**: Complete SMTP email notification system with OAuth2 Microsoft 365 and basic authentication support. Sends automatic alerts when leads are created from public assessments. Features centralized SMTP configuration at `/admin/parametros/smtp`, encrypted credential storage, per-assessment recipient configuration, and professional HTML email templates. Critical OAuth2 bug fixed (base64 encoding instead of hex for XOAUTH2). Includes deployment script `deploy_email_notifications.sh` and comprehensive documentation in `README_EMAIL_NOTIFICATIONS.md`.

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
- **MSAL**: Microsoft Authentication Library for OAuth2 email sending.