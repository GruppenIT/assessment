/**
 * Sistema de Assessment de Cibersegurança
 * JavaScript para funcionalidades do assessment
 */

document.addEventListener('DOMContentLoaded', function() {
    initializeAssessment();
});

/**
 * Inicializa as funcionalidades do assessment
 */
function initializeAssessment() {
    setupAutoSave();
    setupNotaSelection();
    setupProgressTracking();
}

/**
 * Configura o salvamento automático das respostas
 */
function setupAutoSave() {
    const forms = document.querySelectorAll('.resposta-form');
    
    forms.forEach(form => {
        const perguntaId = form.querySelector('input[name="pergunta_id"]').value;
        const notaRadios = form.querySelectorAll('.nota-radio');
        const comentarioTextarea = form.querySelector('.comentario-textarea');
        const btnSalvar = form.querySelector('.btn-salvar');
        const statusElement = form.querySelector('.status-resposta');
        
        // Configurar eventos para os radio buttons de nota
        notaRadios.forEach(radio => {
            radio.addEventListener('change', function() {
                enableSaveButton(btnSalvar);
                autoSaveResposta(perguntaId, form, statusElement, btnSalvar);
            });
        });
        
        // Configurar evento para o textarea de comentário
        let commentTimer;
        comentarioTextarea.addEventListener('input', function() {
            enableSaveButton(btnSalvar);
            
            // Debounce para evitar muitas requisições
            clearTimeout(commentTimer);
            commentTimer = setTimeout(() => {
                const notaSelecionada = form.querySelector('.nota-radio:checked');
                if (notaSelecionada) {
                    autoSaveResposta(perguntaId, form, statusElement, btnSalvar);
                }
            }, 1000);
        });
        
        // Configurar botão de salvar manual
        btnSalvar.addEventListener('click', function() {
            const notaSelecionada = form.querySelector('.nota-radio:checked');
            if (notaSelecionada) {
                saveResposta(perguntaId, form, statusElement, btnSalvar);
            } else {
                showAlert('Por favor, selecione uma nota antes de salvar.', 'warning');
            }
        });
    });
}

/**
 * Configura a seleção visual das notas
 */
function setupNotaSelection() {
    const notaRadios = document.querySelectorAll('.nota-radio');
    
    notaRadios.forEach(radio => {
        radio.addEventListener('change', function() {
            // Remover seleção visual dos outros radios do mesmo grupo
            const formGroup = this.closest('.resposta-form');
            const allRadios = formGroup.querySelectorAll('.nota-radio');
            
            allRadios.forEach(r => {
                r.nextElementSibling.classList.remove('btn-primary');
                r.nextElementSibling.classList.add('btn-outline-primary');
            });
            
            // Aplicar seleção visual ao radio selecionado
            this.nextElementSibling.classList.remove('btn-outline-primary');
            this.nextElementSibling.classList.add('btn-primary');
            
            // Adicionar efeito visual
            this.nextElementSibling.style.transform = 'scale(1.05)';
            setTimeout(() => {
                this.nextElementSibling.style.transform = 'scale(1)';
            }, 150);
        });
    });
}

/**
 * Configura o acompanhamento do progresso
 */
function setupProgressTracking() {
    // Inicializar com valores atuais
    updateProgress();
    
    // Configurar observer para mudanças nas respostas
    const observer = new MutationObserver(function(mutations) {
        mutations.forEach(function(mutation) {
            if (mutation.type === 'childList' || mutation.type === 'attributes') {
                updateProgress();
            }
        });
    });
    
    // Observar mudanças nos elementos de status
    const statusElements = document.querySelectorAll('.status-resposta');
    statusElements.forEach(element => {
        observer.observe(element, { childList: true, subtree: true });
    });
}

/**
 * Salva uma resposta automaticamente
 */
function autoSaveResposta(perguntaId, form, statusElement, btnSalvar) {
    saveResposta(perguntaId, form, statusElement, btnSalvar, true);
}

/**
 * Salva uma resposta no servidor
 */
function saveResposta(perguntaId, form, statusElement, btnSalvar, isAutoSave = false) {
    const notaSelecionada = form.querySelector('.nota-radio:checked');
    const comentario = form.querySelector('.comentario-textarea').value.trim();
    
    if (!notaSelecionada) {
        if (!isAutoSave) {
            showAlert('Por favor, selecione uma nota.', 'warning');
        }
        return;
    }
    
    const nota = parseInt(notaSelecionada.value);
    
    // Mostrar loading no botão
    const originalText = btnSalvar.innerHTML;
    btnSalvar.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>Salvando...';
    btnSalvar.disabled = true;
    
    // Dados para envio
    const dados = {
        pergunta_id: parseInt(perguntaId),
        nota: nota,
        comentario: comentario
    };
    
    // Enviar via fetch
    fetch('/cliente/assessment/salvar', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCSRFToken()
        },
        body: JSON.stringify(dados)
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            // Atualizar status visual
            statusElement.innerHTML = `
                <small class="text-success">
                    <i class="fas fa-check-circle me-1"></i>
                    ${isAutoSave ? 'Salvo automaticamente' : 'Resposta salva'}
                </small>
            `;
            
            // Atualizar progresso geral
            updateProgressBar(data.progresso);
            
            // Marcar pergunta como respondida
            markQuestionAsAnswered(form);
            
            if (!isAutoSave) {
                showAlert('Resposta salva com sucesso!', 'success');
            }
        } else {
            statusElement.innerHTML = `
                <small class="text-danger">
                    <i class="fas fa-exclamation-circle me-1"></i>
                    Erro ao salvar: ${data.message}
                </small>
            `;
            
            if (!isAutoSave) {
                showAlert('Erro ao salvar resposta: ' + data.message, 'danger');
            }
        }
    })
    .catch(error => {
        console.error('Erro:', error);
        statusElement.innerHTML = `
            <small class="text-danger">
                <i class="fas fa-exclamation-circle me-1"></i>
                Erro de conexão
            </small>
        `;
        
        if (!isAutoSave) {
            showAlert('Erro de conexão. Tente novamente.', 'danger');
        }
    })
    .finally(() => {
        // Restaurar botão
        btnSalvar.innerHTML = originalText;
        btnSalvar.disabled = false;
    });
}

/**
 * Habilita o botão de salvar
 */
function enableSaveButton(btnSalvar) {
    btnSalvar.disabled = false;
    btnSalvar.classList.remove('btn-secondary');
    btnSalvar.classList.add('btn-primary');
}

/**
 * Marca uma pergunta como respondida visualmente
 */
function markQuestionAsAnswered(form) {
    const card = form.closest('.pergunta-card');
    const header = card.querySelector('.card-header');
    
    // Adicionar badge de respondida se não existir
    let badge = header.querySelector('.badge-success');
    if (!badge) {
        badge = document.createElement('span');
        badge.className = 'badge bg-success';
        badge.innerHTML = '<i class="fas fa-check me-1"></i>Respondida';
        header.querySelector('.d-flex').appendChild(badge);
    }
    
    // Adicionar classe de status
    card.classList.add('status-respondida');
}

/**
 * Atualiza a barra de progresso
 */
function updateProgressBar(novoProgresso) {
    const progressBar = document.getElementById('progressBar');
    const progressoBadge = document.getElementById('progressoBadge');
    
    if (progressBar && progressoBadge) {
        progressBar.style.width = novoProgresso + '%';
        progressBar.setAttribute('aria-valuenow', novoProgresso);
        progressoBadge.textContent = novoProgresso.toFixed(1) + '%';
    }
}

/**
 * Atualiza o progresso geral
 */
function updateProgress() {
    const totalPerguntas = document.querySelectorAll('.pergunta-card').length;
    const perguntasRespondidas = document.querySelectorAll('.status-respondida').length;
    const respostasCount = document.getElementById('respostasCount');
    
    if (respostasCount) {
        respostasCount.textContent = perguntasRespondidas;
    }
    
    if (totalPerguntas > 0) {
        const progresso = (perguntasRespondidas / totalPerguntas) * 100;
        updateProgressBar(progresso);
    }
}

/**
 * Obtém o token CSRF
 */
function getCSRFToken() {
    const token = document.querySelector('meta[name="csrf-token"]');
    return token ? token.getAttribute('content') : '';
}

/**
 * Mostra um alerta na página
 */
function showAlert(message, type = 'info') {
    // Remover alertas existentes
    const existingAlerts = document.querySelectorAll('.alert-auto');
    existingAlerts.forEach(alert => alert.remove());
    
    // Criar novo alerta
    const alertDiv = document.createElement('div');
    alertDiv.className = `alert alert-${type} alert-dismissible fade show alert-auto`;
    alertDiv.setAttribute('role', 'alert');
    
    const icon = getAlertIcon(type);
    alertDiv.innerHTML = `
        <i class="fas fa-${icon} me-2"></i>
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
    `;
    
    // Inserir no topo da página
    const container = document.querySelector('.container');
    container.insertBefore(alertDiv, container.firstChild);
    
    // Auto-remover após 5 segundos
    setTimeout(() => {
        if (alertDiv.parentNode) {
            alertDiv.remove();
        }
    }, 5000);
}

/**
 * Obtém o ícone apropriado para o tipo de alerta
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
 * Scroll suave para próxima pergunta não respondida
 */
function scrollToNextQuestion() {
    const perguntasNaoRespondidas = document.querySelectorAll('.pergunta-card:not(.status-respondida)');
    
    if (perguntasNaoRespondidas.length > 0) {
        perguntasNaoRespondidas[0].scrollIntoView({
            behavior: 'smooth',
            block: 'center'
        });
    }
}

/**
 * Adiciona atalhos de teclado para melhor UX
 */
document.addEventListener('keydown', function(event) {
    // Ctrl + S para salvar resposta atual
    if (event.ctrlKey && event.key === 's') {
        event.preventDefault();
        const activeForm = document.activeElement.closest('.resposta-form');
        if (activeForm) {
            const btnSalvar = activeForm.querySelector('.btn-salvar');
            if (!btnSalvar.disabled) {
                btnSalvar.click();
            }
        }
    }
    
    // Teclas numéricas (0-5) para seleção rápida de nota
    if (event.key >= '0' && event.key <= '5') {
        const activeForm = document.activeElement.closest('.resposta-form');
        if (activeForm && activeForm.querySelector('textarea') !== document.activeElement) {
            const perguntaId = activeForm.querySelector('input[name="pergunta_id"]').value;
            const notaRadio = document.getElementById(`nota_${perguntaId}_${event.key}`);
            if (notaRadio) {
                notaRadio.checked = true;
                notaRadio.dispatchEvent(new Event('change'));
            }
        }
    }
});

/**
 * Confirma antes de sair da página se há mudanças não salvas
 */
window.addEventListener('beforeunload', function(event) {
    const buttonsEnabled = document.querySelectorAll('.btn-salvar:not(:disabled)');
    
    if (buttonsEnabled.length > 0) {
        event.preventDefault();
        event.returnValue = 'Você tem respostas não salvas. Tem certeza que deseja sair?';
        return event.returnValue;
    }
});
