# Sistema de Avaliações de Maturidade

## Overview

This is a Flask-based web application for multi-type maturity assessments. The system allows administrators to manage different types of assessments (cybersecurity, compliance, etc.), register clients with multiple respondents, and provides comprehensive assessment capabilities. Built using the MVC (Model-View-Controller) pattern, the application features multi-level authentication, role-based access control, CSV bulk import, and comprehensive reporting capabilities.

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
- **Usuario**: Administrative users only with password hashing
- **TipoAssessment**: Different types of assessments (Cybersecurity, Compliance, etc.)
- **Cliente**: Client companies with business information and logo
- **Respondente**: Client's employees who answer assessments with individual logins
- **Dominio**: Assessment domains organized by type
- **Pergunta**: Assessment questions linked to domains
- **Resposta**: Respondent answers with 0-5 rating scale and optional comments
- **ClienteAssessment**: Association between clients and assessment types
- **Logo**: Company logo management for branding

### Routes (`/routes/`)
- **auth**: Administrative authentication (admin login only)
- **admin**: Administrative functions (assessment types, domains, questions, client management, CSV import)
- **respondente**: Respondent authentication and assessment interface
- **cliente**: Client management and association with assessment types
- **relatorio**: Report generation and visualization

### Forms (`/forms/`)
- **auth_forms**: Administrative login forms with validation
- **admin_forms**: Administrative forms for content management (domains, questions, types)
- **cliente_forms**: Client management, respondent creation, and CSV import forms
- **assessment_forms**: Assessment response forms with rating system

### Utilities (`/utils/`)
- **auth_utils**: Role-based access control decorators
- **pdf_utils**: PDF report generation using ReportLab
- **upload_utils**: File upload handling with security measures
- **csv_utils**: CSV bulk import processing for domains and questions

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

## Development Workflow

### Git Integration Setup
- Created automated Git workflow for continuous development
- Setup scripts for repository initialization and configuration
- Deploy automation for Ubuntu servers with rollback capability
- Requirements.txt generation for production consistency

### Development Process
1. **Development Environment**: Work on improvements in Replit
2. **Version Control**: Use Git for tracking changes and releases  
3. **Production Deploy**: Automated deployment to Ubuntu server via script
4. **Monitoring**: Comprehensive logging and status checking tools

### Key Scripts
- `setup-git.sh`: Initialize Git repository with proper configuration
- `deploy.sh`: Automated deployment script for Ubuntu servers
- `generate-requirements.py`: Create production-ready requirements.txt
- `dev-workflow.md`: Complete development workflow documentation

## Changelog
- July 07, 2025. Initial setup
- July 11, 2025. Major architecture overhaul:
  - Renamed to "Sistema de Avaliações de Maturidade"
  - Added TipoAssessment model for multiple assessment types
  - Created Cliente and Respondente models (separated from Usuario)
  - Implemented CSV bulk import functionality
  - Added client-respondent relationship management
  - Removed public client registration (admin-only now)
  - Enhanced client data with business fields (razão social, localidade, segmento)
- July 14, 2025. Complete system implementation:
  - Added Git integration and version control setup
  - Created automated deployment system for Ubuntu servers
  - Implemented client-assessment association management interface
  - Fixed respondent authentication system with proper Flask-WTF forms
  - Created comprehensive assessment interface with auto-save functionality
  - Implemented maturity rating system (0-5) with proper descriptions:
    * 0 - Inexistente: nenhum controle implementado
    * 1 - Inicial: práticas informais e não documentadas
    * 2 - Básico: controles definidos, aplicação inconsistente
    * 3 - Intermediário: controles padronizados e repetíveis
    * 4 - Avançado: controles monitorados com métricas
    * 5 - Otimizado: controles integrados e melhorados continuamente
  - Added real-time progress tracking and visual feedback system
  - Implemented multi-respondent tracking system with individual response attribution
  - Created admin interface to view responses separated by respondent
  - Fixed admin assessments overview page to work with new Cliente/Respondente structure
  - Added complete client editing interface with logo upload functionality
  - Enhanced PDF reports with radar charts, detailed domain analysis, and professional formatting
  - Fixed deployment issues for on-premise environment with proper module structure
  - **CRITICAL FIX**: Resolved major project listing authentication issue that prevented projects from appearing in admin interface. Created bypass solution with direct SQL queries and functional HTML output. Projects now display correctly with all data.
  - **DEFINITIVE SOLUTION**: Made `/admin/projetos/working` the default route for project listing. Main route now redirects to working version, ensuring all projects including newly created ones appear correctly without authentication conflicts.
- July 15, 2025. Respondent Architecture Overhaul and Assessment Versioning:
  - **RESPONDENT ARCHITECTURE OVERHAUL**: Implemented email-agnostic login system
  - Added `login` field to respondents table (unique globally)
  - Removed email uniqueness constraint - same email can exist across different clients
  - Updated authentication to accept both email and login for respondent access
  - Created client-specific login patterns (e.g., rodrigo.melnick for Melnick client, rodrigo.teste for Teste client)
  - Enhanced forms and templates to include login field with contextual hints
  - Resolved CSRF validation issues in respondent creation process
- July 15, 2025. Assessment Versioning System Implementation:
  - **MAJOR ARCHITECTURE CHANGE**: Implemented centralized assessment versioning system
  - Created new models: AssessmentTipo, AssessmentVersao, AssessmentDominio for version control
  - Implemented draft → published → archived workflow for assessment versions
  - Created comprehensive admin interface for assessment management
  - Reorganized navigation: moved assessment management under "Configurações" dropdown
  - Added CSV import functionality that creates new draft versions
  - Maintained backward compatibility with existing system through nullable foreign keys
  - Projects now maintain their opening assessment version throughout lifecycle
  - New projects use latest published version, existing projects keep their version
  - **INTERFACE REORGANIZATION**: Consolidated admin menu with dropdown structure for better UX
  - **DATABASE MIGRATION**: Fixed route conflicts and migrated existing assessment types (Cibersegurança, LGPD) to new versioning system with all domains and questions preserved
- July 15, 2025. Logo System and Project Filtering Fixes:
  - **LOGO URL GENERATION FIX**: Corrected logo URL generation issues in production environment
  - Fixed system logo URL generation preventing duplicate path concatenation (logos/logos/ → logos/)
  - Updated client logo display to use correct uploaded_file route instead of static route
  - Fixed upload_logo route to store clean file paths without duplicate subfolder names
  - Enhanced project filtering system with client-specific views
  - **PROJECT FILTERING**: Implemented client-specific project filtering with `?cliente=ID` parameter
  - Added visual indicators for filtered vs. general project views
  - Created contextual navigation buttons for filtered project management
  - Fixed template rendering to show client context in project listings
- July 15, 2025. Dashboard Reconstruction and Database Reset:
  - **DASHBOARD COMPLETE OVERHAUL**: Rebuilt admin dashboard with comprehensive timezone integration
  - Implemented pytz timezone conversion system with GMT-3 Brazil as default
  - Added real-time statistics: clients, projects, respondents, assessment types, responses
  - Created activity tracking system showing daily response patterns
  - Enhanced project progress display with collaborative progress calculation
  - Added assessment type statistics with project usage and response counts
  - Implemented intelligent alerts system for projects without respondents
  - Fixed template variable consistency (stats vs estatisticas) for proper rendering
  - **DATABASE RESET**: Cleaned all test data for fresh start
  - Removed all clients, projects, respondents, responses, assessment types
  - Cleared assessment versioning data and dependencies
  - Database now ready for comprehensive testing with new data structure
- July 15, 2025. Project Creation System Integration Fix:
  - **FIXED PROJECT CREATION WITH NEW VERSIONING**: Resolved conflict between old and new assessment systems
  - Fixed ProjetoForm to use AssessmentTipo from new versioning system (assessment_tipos table)
  - Updated project creation route to use versao_assessment_id instead of deprecated tipo_assessment_id
  - Modified database schema to allow nullable tipo_assessment_id for backward compatibility
  - Projects now correctly associate with published assessment versions
  - Assessment types created via CSV import now properly display in project creation forms
  - **SYSTEM INTEGRATION**: Seamless integration between assessment versioning and project management
  - Fixed foreign key constraints allowing both old and new system coexistence
  - Validated successful project creation with assessment type "Cibersegurança (NIST / ISO27001 / CIS)"

## User Preferences

Preferred communication style: Simple, everyday language.