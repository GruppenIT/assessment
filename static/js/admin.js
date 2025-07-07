/**
 * Sistema de Assessment de Cibersegurança
 * JavaScript para funcionalidades administrativas
 */

document.addEventListener('DOMContentLoaded', function() {
    initializeAdminFunctions();
});

/**
 * Inicializa todas as funcionalidades administrativas
 */
function initializeAdminFunctions() {
    setupFormValidations();
    setupConfirmationDialogs();
    setupDynamicForms();
    setupFileUpload();
    setupDataTables();
    setupCharts();
    setupAutoRefresh();
}

/**
 * Configura validações de formulários
 */
function setupFormValidations() {
    // Validação para formulário de domínio
    const dominioForms = document.querySelectorAll('form[action*="dominio"]');
    dominioForms.forEach(form => {
        form.addEventListener('submit', function(e) {
            const nome = form.querySelector('input[name="nome"]');
            const ordem = form.querySelector('input[name="ordem"]');
            
            if (!validateDominioForm(nome, ordem)) {
                e.preventDefault();
            }
        });
    });
    
    // Validação para formulário de pergunta
    const perguntaForms = document.querySelectorAll('form[action*="pergunta"]');
    perguntaForms.forEach(form => {
        form.addEventListener('submit', function(e) {
            const dominioId = form.querySelector('select[name="dominio_id"]');
            const texto = form.querySelector('textarea[name="texto"]');
            
            if (!validatePerguntaForm(dominioId, texto)) {
                e.preventDefault();
            }
        });
    });
    
    // Validação em tempo real
    setupRealTimeValidation();
}

/**
 * Valida formulário de domínio
 */
function validateDominioForm(nomeField, ordemField) {
    let isValid = true;
    
    // Limpar mensagens anteriores
    clearFieldErrors(nomeField);
    clearFieldErrors(ordemField);
    
    // Validar nome
    if (!nomeField.value.trim()) {
        showFieldError(nomeField, 'Nome do domínio é obrigatório');
        isValid = false;
    } else if (nomeField.value.trim().length < 2) {
        showFieldError(nomeField, 'Nome deve ter pelo menos 2 caracteres');
        isValid = false;
    }
    
    // Validar ordem
    const ordem = parseInt(ordemField.value);
    if (isNaN(ordem) || ordem < 1) {
        showFieldError(ordemField, 'Ordem deve ser um número maior que 0');
        isValid = false;
    }
    
    return isValid;
}

/**
 * Valida formulário de pergunta
 */
function validatePerguntaForm(dominioField, textoField) {
    let isValid = true;
    
    // Limpar mensagens anteriores
    clearFieldErrors(dominioField);
    clearFieldErrors(textoField);
    
    // Validar domínio
    if (!dominioField.value) {
        showFieldError(dominioField, 'Selecione um domínio');
        isValid = false;
    }
    
    // Validar texto
    if (!textoField.value.trim()) {
        showFieldError(textoField, 'Texto da pergunta é obrigatório');
        isValid = false;
    } else if (textoField.value.trim().length < 10) {
        showFieldError(textoField, 'Texto deve ter pelo menos 10 caracteres');
        isValid = false;
    }
    
    return isValid;
}

/**
 * Configura validação em tempo real
 */
function setupRealTimeValidation() {
    // Validação de nome de domínio
    const nomeInputs = document.querySelectorAll('input[name="nome"]');
    nomeInputs.forEach(input => {
        input.addEventListener('blur', function() {
            if (this.value.trim() && this.value.trim().length < 2) {
                showFieldError(this, 'Nome deve ter pelo menos 2 caracteres');
            } else {
                clearFieldErrors(this);
            }
        });
    });
    
    // Validação de ordem
    const ordemInputs = document.querySelectorAll('input[name="ordem"]');
    ordemInputs.forEach(input => {
        input.addEventListener('blur', function() {
            const valor = parseInt(this.value);
            if (isNaN(valor) || valor < 1) {
                showFieldError(this, 'Ordem deve ser um número maior que 0');
            } else {
                clearFieldErrors(this);
            }
        });
    });
    
    // Contador de caracteres para textareas
    const textareas = document.querySelectorAll('textarea');
    textareas.forEach(textarea => {
        setupCharacterCounter(textarea);
    });
}

/**
 * Configura contador de caracteres
 */
function setupCharacterCounter(textarea) {
    const maxLength = textarea.getAttribute('maxlength');
    if (!maxLength) return;
    
    const counter = document.createElement('div');
    counter.className = 'form-text text-end';
    counter.id = textarea.id + '_counter';
    
    textarea.parentNode.appendChild(counter);
    
    function updateCounter() {
        const remaining = maxLength - textarea.value.length;
        counter.textContent = `${textarea.value.length}/${maxLength} caracteres`;
        
        if (remaining < 50) {
            counter.className = 'form-text text-end text-warning';
        } else if (remaining < 20) {
            counter.className = 'form-text text-end text-danger';
        } else {
            counter.className = 'form-text text-end text-muted';
        }
    }
    
    textarea.addEventListener('input', updateCounter);
    updateCounter();
}

/**
 * Mostra erro em campo específico
 */
function showFieldError(field, message) {
    clearFieldErrors(field);
    
    field.classList.add('is-invalid');
    
    const errorDiv = document.createElement('div');
    errorDiv.className = 'invalid-feedback';
    errorDiv.textContent = message;
    
    field.parentNode.appendChild(errorDiv);
}

/**
 * Limpa erros de um campo
 */
function clearFieldErrors(field) {
    field.classList.remove('is-invalid');
    
    const errorElements = field.parentNode.querySelectorAll('.invalid-feedback');
    errorElements.forEach(element => element.remove());
}

/**
 * Configura diálogos de confirmação
 */
function setupConfirmationDialogs() {
    // Confirmação para exclusões
    const deleteButtons = document.querySelectorAll('button[onclick*="confirmarExclusao"]');
    deleteButtons.forEach(button => {
        button.addEventListener('click', function(e) {
            e.preventDefault();
            const onclick = this.getAttribute('onclick');
            eval(onclick);
        });
    });
    
    // Confirmação para ações críticas
    const criticalActions = document.querySelectorAll('.btn-danger[type="submit"]');
    criticalActions.forEach(button => {
        button.addEventListener('click', function(e) {
            if (!confirm('Tem certeza que deseja realizar esta ação? Esta operação não pode ser desfeita.')) {
                e.preventDefault();
            }
        });
    });
}

/**
 * Configura formulários dinâmicos
 */
function setupDynamicForms() {
    // Auto-submit para filtros
    const filterSelects = document.querySelectorAll('select[onchange*="filtrar"]');
    filterSelects.forEach(select => {
        select.addEventListener('change', function() {
            const onchange = this.getAttribute('onchange');
            eval(onchange);
        });
    });
    
    // Limpar formulários ao fechar modais
    const modals = document.querySelectorAll('.modal');
    modals.forEach(modal => {
        modal.addEventListener('hidden.bs.modal', function() {
            const forms = this.querySelectorAll('form');
            forms.forEach(form => {
                form.reset();
                
                // Limpar erros de validação
                const invalidFields = form.querySelectorAll('.is-invalid');
                invalidFields.forEach(field => clearFieldErrors(field));
            });
        });
    });
    
    // Auto-focus em primeiro campo dos modais
    modals.forEach(modal => {
        modal.addEventListener('shown.bs.modal', function() {
            const firstInput = this.querySelector('input:not([type="hidden"]), select, textarea');
            if (firstInput) {
                firstInput.focus();
            }
        });
    });
}

/**
 * Configura upload de arquivos
 */
function setupFileUpload() {
    const fileInputs = document.querySelectorAll('input[type="file"]');
    
    fileInputs.forEach(input => {
        input.addEventListener('change', function() {
            validateFileUpload(this);
            previewFile(this);
        });
        
        // Drag and drop
        setupDragAndDrop(input);
    });
}

/**
 * Valida upload de arquivo
 */
function validateFileUpload(input) {
    const file = input.files[0];
    if (!file) return;
    
    const allowedTypes = ['image/png', 'image/jpeg', 'image/jpg', 'image/gif'];
    const maxSize = 16 * 1024 * 1024; // 16MB
    
    // Validar tipo
    if (!allowedTypes.includes(file.type)) {
        showAlert('Tipo de arquivo não permitido. Use apenas PNG, JPG ou GIF.', 'danger');
        input.value = '';
        return false;
    }
    
    // Validar tamanho
    if (file.size > maxSize) {
        showAlert('Arquivo muito grande. Tamanho máximo: 16MB.', 'danger');
        input.value = '';
        return false;
    }
    
    return true;
}

/**
 * Preview de arquivo
 */
function previewFile(input) {
    const file = input.files[0];
    if (!file || !file.type.startsWith('image/')) return;
    
    const reader = new FileReader();
    reader.onload = function(e) {
        // Procurar por preview existente ou criar novo
        let preview = document.getElementById('file-preview');
        if (!preview) {
            preview = document.createElement('div');
            preview.id = 'file-preview';
            preview.className = 'mt-3';
            input.parentNode.appendChild(preview);
        }
        
        preview.innerHTML = `
            <div class="text-center">
                <img src="${e.target.result}" alt="Preview" class="img-fluid border rounded" style="max-height: 150px;">
                <div class="small text-muted mt-1">
                    ${file.name} (${formatFileSize(file.size)})
                </div>
            </div>
        `;
    };
    reader.readAsDataURL(file);
}

/**
 * Configura drag and drop
 */
function setupDragAndDrop(input) {
    const dropZone = input.parentNode;
    
    ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
        dropZone.addEventListener(eventName, preventDefaults, false);
    });
    
    ['dragenter', 'dragover'].forEach(eventName => {
        dropZone.addEventListener(eventName, () => dropZone.classList.add('drag-over'), false);
    });
    
    ['dragleave', 'drop'].forEach(eventName => {
        dropZone.addEventListener(eventName, () => dropZone.classList.remove('drag-over'), false);
    });
    
    dropZone.addEventListener('drop', function(e) {
        const files = e.dataTransfer.files;
        if (files.length > 0) {
            input.files = files;
            input.dispatchEvent(new Event('change'));
        }
    });
}

/**
 * Previne comportamento padrão de eventos
 */
function preventDefaults(e) {
    e.preventDefault();
    e.stopPropagation();
}

/**
 * Formata tamanho de arquivo
 */
function formatFileSize(bytes) {
    if (bytes === 0) return '0 Bytes';
    
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

/**
 * Configura tabelas de dados
 */
function setupDataTables() {
    // Ordenação de tabelas
    const sortableHeaders = document.querySelectorAll('th[data-sort]');
    sortableHeaders.forEach(header => {
        header.style.cursor = 'pointer';
        header.addEventListener('click', function() {
            sortTable(this);
        });
    });
    
    // Filtros de tabela
    const searchInputs = document.querySelectorAll('input[data-table-search]');
    searchInputs.forEach(input => {
        input.addEventListener('input', function() {
            filterTable(this);
        });
    });
    
    // Paginação se necessário
    setupTablePagination();
}

/**
 * Ordena tabela por coluna
 */
function sortTable(header) {
    const table = header.closest('table');
    const tbody = table.querySelector('tbody');
    const rows = Array.from(tbody.querySelectorAll('tr'));
    const columnIndex = Array.from(header.parentNode.children).indexOf(header);
    const sortType = header.dataset.sort;
    
    // Determinar direção da ordenação
    const isAsc = !header.classList.contains('sort-asc');
    
    // Remover classes de ordenação de todos os headers
    table.querySelectorAll('th').forEach(th => {
        th.classList.remove('sort-asc', 'sort-desc');
    });
    
    // Adicionar classe de ordenação ao header atual
    header.classList.add(isAsc ? 'sort-asc' : 'sort-desc');
    
    // Ordenar rows
    rows.sort((a, b) => {
        const aValue = a.children[columnIndex].textContent.trim();
        const bValue = b.children[columnIndex].textContent.trim();
        
        let comparison = 0;
        
        if (sortType === 'number') {
            comparison = parseFloat(aValue) - parseFloat(bValue);
        } else if (sortType === 'date') {
            comparison = new Date(aValue) - new Date(bValue);
        } else {
            comparison = aValue.localeCompare(bValue);
        }
        
        return isAsc ? comparison : -comparison;
    });
    
    // Reordenar DOM
    rows.forEach(row => tbody.appendChild(row));
}

/**
 * Filtra tabela
 */
function filterTable(input) {
    const tableId = input.dataset.tableSearch;
    const table = document.getElementById(tableId);
    if (!table) return;
    
    const filter = input.value.toLowerCase();
    const rows = table.querySelectorAll('tbody tr');
    
    rows.forEach(row => {
        const text = row.textContent.toLowerCase();
        row.style.display = text.includes(filter) ? '' : 'none';
    });
}

/**
 * Configura paginação de tabela
 */
function setupTablePagination() {
    const paginatedTables = document.querySelectorAll('table[data-paginate]');
    
    paginatedTables.forEach(table => {
        const rowsPerPage = parseInt(table.dataset.paginate) || 10;
        createPagination(table, rowsPerPage);
    });
}

/**
 * Cria paginação para tabela
 */
function createPagination(table, rowsPerPage) {
    const tbody = table.querySelector('tbody');
    const rows = Array.from(tbody.querySelectorAll('tr'));
    const totalPages = Math.ceil(rows.length / rowsPerPage);
    
    if (totalPages <= 1) return;
    
    let currentPage = 1;
    
    // Criar controles de paginação
    const paginationContainer = document.createElement('div');
    paginationContainer.className = 'pagination-container mt-3';
    table.parentNode.appendChild(paginationContainer);
    
    function showPage(page) {
        const start = (page - 1) * rowsPerPage;
        const end = start + rowsPerPage;
        
        rows.forEach((row, index) => {
            row.style.display = (index >= start && index < end) ? '' : 'none';
        });
        
        updatePaginationControls();
    }
    
    function updatePaginationControls() {
        paginationContainer.innerHTML = `
            <nav aria-label="Paginação da tabela">
                <ul class="pagination pagination-sm justify-content-center">
                    <li class="page-item ${currentPage === 1 ? 'disabled' : ''}">
                        <button class="page-link" onclick="changePage(${currentPage - 1})" ${currentPage === 1 ? 'disabled' : ''}>
                            <i class="fas fa-chevron-left"></i>
                        </button>
                    </li>
                    ${generatePageNumbers()}
                    <li class="page-item ${currentPage === totalPages ? 'disabled' : ''}">
                        <button class="page-link" onclick="changePage(${currentPage + 1})" ${currentPage === totalPages ? 'disabled' : ''}>
                            <i class="fas fa-chevron-right"></i>
                        </button>
                    </li>
                </ul>
            </nav>
            <div class="text-center small text-muted">
                Mostrando ${((currentPage - 1) * rowsPerPage) + 1} a ${Math.min(currentPage * rowsPerPage, rows.length)} de ${rows.length} registros
            </div>
        `;
    }
    
    function generatePageNumbers() {
        let html = '';
        const maxVisible = 5;
        
        let start = Math.max(1, currentPage - Math.floor(maxVisible / 2));
        let end = Math.min(totalPages, start + maxVisible - 1);
        
        if (end - start + 1 < maxVisible) {
            start = Math.max(1, end - maxVisible + 1);
        }
        
        for (let i = start; i <= end; i++) {
            html += `
                <li class="page-item ${i === currentPage ? 'active' : ''}">
                    <button class="page-link" onclick="changePage(${i})">${i}</button>
                </li>
            `;
        }
        
        return html;
    }
    
    // Função global para mudança de página
    window.changePage = function(page) {
        if (page >= 1 && page <= totalPages) {
            currentPage = page;
            showPage(currentPage);
        }
    };
    
    // Mostrar primeira página
    showPage(1);
}

/**
 * Configura gráficos para dashboard
 */
function setupCharts() {
    // Verificar se Chart.js está disponível
    if (typeof Chart === 'undefined') return;
    
    // Gráfico de progresso de assessments
    const progressChart = document.getElementById('progressChart');
    if (progressChart) {
        createProgressChart(progressChart);
    }
    
    // Gráfico de distribuição de notas
    const distributionChart = document.getElementById('distributionChart');
    if (distributionChart) {
        createDistributionChart(distributionChart);
    }
}

/**
 * Cria gráfico de progresso
 */
function createProgressChart(canvas) {
    // Dados de exemplo - em produção viriam do servidor
    const data = {
        labels: ['Completos', 'Em Andamento', 'Não Iniciados'],
        datasets: [{
            data: [12, 5, 8],
            backgroundColor: ['#28a745', '#ffc107', '#6c757d'],
            borderWidth: 0
        }]
    };
    
    new Chart(canvas, {
        type: 'doughnut',
        data: data,
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'bottom'
                }
            }
        }
    });
}

/**
 * Cria gráfico de distribuição
 */
function createDistributionChart(canvas) {
    const data = {
        labels: ['0', '1', '2', '3', '4', '5'],
        datasets: [{
            label: 'Quantidade de Respostas',
            data: [15, 25, 30, 35, 20, 10],
            backgroundColor: '#007bff',
            borderColor: '#0056b3',
            borderWidth: 1
        }]
    };
    
    new Chart(canvas, {
        type: 'bar',
        data: data,
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                y: {
                    beginAtZero: true
                }
            },
            plugins: {
                legend: {
                    display: false
                }
            }
        }
    });
}

/**
 * Configura auto-refresh para dados dinâmicos
 */
function setupAutoRefresh() {
    // Auto-refresh para dashboard (apenas se na página de dashboard)
    if (window.location.pathname.includes('/admin/dashboard')) {
        setInterval(refreshDashboardStats, 30000); // 30 segundos
    }
    
    // Auto-refresh para assessments
    if (window.location.pathname.includes('/admin/assessments')) {
        setInterval(refreshAssessmentsTable, 60000); // 1 minuto
    }
}

/**
 * Atualiza estatísticas do dashboard
 */
function refreshDashboardStats() {
    // Implementar requisição AJAX para atualizar stats
    // Por enquanto apenas log
    console.log('Atualizando estatísticas do dashboard...');
}

/**
 * Atualiza tabela de assessments
 */
function refreshAssessmentsTable() {
    // Implementar requisição AJAX para atualizar tabela
    console.log('Atualizando tabela de assessments...');
}

/**
 * Mostra alerta na página
 */
function showAlert(message, type = 'info', duration = 5000) {
    // Remover alertas existentes
    const existingAlerts = document.querySelectorAll('.alert-admin-js');
    existingAlerts.forEach(alert => alert.remove());
    
    // Criar novo alerta
    const alertDiv = document.createElement('div');
    alertDiv.className = `alert alert-${type} alert-dismissible fade show alert-admin-js`;
    alertDiv.setAttribute('role', 'alert');
    
    const icon = getAlertIcon(type);
    alertDiv.innerHTML = `
        <i class="fas fa-${icon} me-2"></i>
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
    `;
    
    // Inserir no topo da página
    const container = document.querySelector('.container');
    if (container) {
        container.insertBefore(alertDiv, container.firstChild);
        
        // Auto-remover após duração especificada
        if (duration > 0) {
            setTimeout(() => {
                if (alertDiv.parentNode) {
                    alertDiv.remove();
                }
            }, duration);
        }
    }
}

/**
 * Obtém ícone para tipo de alerta
 */
function getAlertIcon(type) {
    const icons = {
        'success': 'check-circle',
        'danger': 'exclamation-circle',
        'warning': 'exclamation-triangle',
        'info': 'info-circle'
    };
    return icons[type] || 'info-circle';
}

/**
 * Utilitários para exportação de dados
 */
const ExportUtils = {
    /**
     * Exporta tabela para CSV
     */
    tableToCSV: function(tableId, filename = 'dados.csv') {
        const table = document.getElementById(tableId);
        if (!table) return;
        
        let csv = [];
        const rows = table.querySelectorAll('tr');
        
        rows.forEach(row => {
            const cols = row.querySelectorAll('td, th');
            const rowData = Array.from(cols).map(col => {
                return '"' + col.textContent.trim().replace(/"/g, '""') + '"';
            });
            csv.push(rowData.join(','));
        });
        
        this.downloadCSV(csv.join('\n'), filename);
    },
    
    /**
     * Download de arquivo CSV
     */
    downloadCSV: function(csv, filename) {
        const csvFile = new Blob([csv], { type: 'text/csv' });
        const downloadLink = document.createElement('a');
        
        downloadLink.download = filename;
        downloadLink.href = window.URL.createObjectURL(csvFile);
        downloadLink.style.display = 'none';
        
        document.body.appendChild(downloadLink);
        downloadLink.click();
        document.body.removeChild(downloadLink);
    }
};

/**
 * Adiciona estilos CSS dinâmicos
 */
function addDynamicStyles() {
    const style = document.createElement('style');
    style.textContent = `
        .drag-over {
            border: 2px dashed #007bff !important;
            background-color: rgba(0, 123, 255, 0.05) !important;
        }
        
        .sort-asc::after {
            content: ' ↑';
            color: #007bff;
        }
        
        .sort-desc::after {
            content: ' ↓';
            color: #007bff;
        }
        
        .table th[data-sort] {
            user-select: none;
        }
        
        .table th[data-sort]:hover {
            background-color: rgba(0, 123, 255, 0.1);
        }
        
        .pagination-container {
            display: flex;
            flex-direction: column;
            align-items: center;
        }
        
        @media (max-width: 768px) {
            .pagination-sm .page-link {
                padding: 0.25rem 0.5rem;
                font-size: 0.875rem;
            }
        }
    `;
    
    document.head.appendChild(style);
}

// Adicionar estilos quando o script carrega
addDynamicStyles();

/**
 * Shortcuts de teclado para administradores
 */
document.addEventListener('keydown', function(event) {
    // Ctrl + Alt + N para novo item (dependendo da página)
    if (event.ctrlKey && event.altKey && event.key === 'n') {
        event.preventDefault();
        
        if (window.location.pathname.includes('/admin/dominios')) {
            const modal = new bootstrap.Modal(document.getElementById('modalNovoDominio'));
            modal.show();
        } else if (window.location.pathname.includes('/admin/perguntas')) {
            const modal = new bootstrap.Modal(document.getElementById('modalNovaPergunta'));
            modal.show();
        }
    }
    
    // Escape para fechar modais
    if (event.key === 'Escape') {
        const openModals = document.querySelectorAll('.modal.show');
        openModals.forEach(modal => {
            const modalInstance = bootstrap.Modal.getInstance(modal);
            if (modalInstance) {
                modalInstance.hide();
            }
        });
    }
});
