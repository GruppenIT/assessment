# Sistema de Avaliações de Maturidade

## Overview
This Flask-based web application provides a comprehensive system for multi-type maturity assessments (e.g., cybersecurity, compliance). It enables administrators to manage various assessment types, register clients with multiple respondents, and conduct detailed assessments. Key features include multi-level authentication, role-based access control, CSV bulk import for content, robust reporting with AI-driven insights, and formal PDF generation. The system is designed following the MVC pattern for modularity and scalability, targeting robust on-premise deployments.

## User Preferences
Preferred communication style: Simple, everyday language.

## System Architecture

### UI/UX Decisions
- **Frontend**: Jinja2 templates, Bootstrap 5 for responsive design, Vanilla JavaScript for interactivity.
- **Icons**: Font Awesome.
- **Admin Dashboard**: Comprehensive dashboard with statistics, activity tracking, and an "Aguarde..." loading interface for AI processes.
- **Public Assessment UI**: Mobile-first design with dark theme, gradient backgrounds, corporate branding (four logos), and progress tracking.
- **Email Templates**: Professional HTML email templates with inline embedded logos.
- **Interactive Charts**: Chart.js visualizations (bar, radar) with score-based color coding and tooltips for group statistics.
- **Real-time Updates**: Auto-refresh functionality for group statistics page with customizable intervals and localStorage persistence.
- **QR Code**: Client-side QR code generation for group access.

### Technical Implementations
- **Backend Framework**: Flask (Python).
- **ORM**: SQLAlchemy with Flask-SQLAlchemy.
- **Database**: PostgreSQL (production), SQLite (development).
- **Authentication**: Flask-Login for session management, Werkzeug for password hashing.
- **Design Pattern**: MVC with Flask Blueprints for modularity.
- **Role-Based Access Control**: Implemented via `auth_utils`.
- **PDF Generation**: ReportLab for formal PDF reports including AI-generated sections.
- **CSV Import**: Bulk import for domains and questions, supporting assessment versioning.
- **AI Integration**: OpenAI for generating report introductions and final considerations, with payload optimization.
- **Email System**: SMTP email sending with OAuth2 Microsoft 365 and basic authentication, lead notification system, encrypted credential storage, and inline logo embedding (CID).
- **Security**: Two-Factor Authentication (TOTP) with QR code setup and backup codes, mandatory password change mechanism.
- **Deployment**: Designed for robust on-premise deployment with `env_loader.py`, unified deployment scripts (`deploy_onpremise_unified.sh`, `deploy_onpremise_com_publico.sh`), and specific fix scripts for profile, password encoding, and email notifications.
- **Assessment Versioning**: Comprehensive system for managing draft, published, and archived assessment states (`AssessmentTipo`, `AssessmentVersao`, `AssessmentDominio`).
- **Public Assessment Flow**: Friction-free user experience where results are shown immediately, and lead capture is an optional email request. Supports shareable URLs with `?group=` parameter for campaign tracking.
- **Group Management**: Grouping based on `TAG + ASSESSMENT TYPE ID`, admin dashboard for managing groups, filtering, deletion, and "General" groups for overall statistics.

### Feature Specifications
- **Models**: `Usuario`, `TipoAssessment`, `Cliente`, `Respondente`, `Dominio`, `Pergunta`, `Resposta`, `ClienteAssessment`, `Logo`, `AssessmentPublico`, `RespostaPublica`, `AssessmentTipo`, `AssessmentVersao`, `AssessmentDominio`.
- **Core Workflows**: Client registration, assessment configuration, respondent invitation, progress tracking, report generation.
- **Forms**: WTForms for authentication, administration, client management, and public assessment responses.
- **Utilities**: `pdf_utils`, `upload_utils`, `csv_utils`, `openai_monitor`, `publico_utils`, `email_utils`, `password_utils`.
- **Project Configuration**: Association of projects with assessment versions, evaluator assignment.
- **Lead Management**: Automated lead creation upon email request in public assessments, cascade deletion of public assessments upon lead removal, cleanup script.
- **Group Statistics**: Interactive charts (vertical bar, horizontal bar, radar, table), score-based color coding, real-time auto-refresh, filters for assessment type and tag, group deletion, QR code generation.

## External Dependencies
- **Flask**: Web framework.
- **SQLAlchemy**: ORM.
- **Flask-Login**: User session management.
- **WTForms**: Form handling.
- **ReportLab**: PDF generation.
- **Bootstrap 5**: CSS framework.
- **Font Awesome**: Icon library.
- **OpenAI API**: AI text generation.
- **Pytz**: Timezone handling.
- **SortableJS**: Drag-and-drop functionality.
- **MSAL**: Microsoft Authentication Library (for OAuth2 email).
- **QRCode.js**: QR code generation (client-side).