/**
 * Interface de "Aguarde..." para processamento OpenAI
 */

class OpenAIProcessingUI {
    constructor() {
        this.modal = null;
        this.progressBar = null;
        this.statusText = null;
        this.detailsText = null;
        this.startTime = null;
        this.estimatedDuration = 0;
        this.currentOperation = '';
        
        this.createModal();
    }
    
    createModal() {
        // Criar modal HTML
        const modalHTML = `
        <div class="modal fade" id="openaiProcessingModal" tabindex="-1" aria-labelledby="openaiProcessingModalLabel" aria-hidden="true" data-bs-backdrop="static" data-bs-keyboard="false">
            <div class="modal-dialog modal-lg">
                <div class="modal-content">
                    <div class="modal-header bg-primary text-white">
                        <h5 class="modal-title" id="openaiProcessingModalLabel">
                            <i class="fas fa-robot me-2"></i>
                            Processamento com Inteligência Artificial
                        </h5>
                    </div>
                    <div class="modal-body text-center py-4">
                        <!-- Ícone animado -->
                        <div class="mb-4">
                            <i class="fas fa-brain fa-3x text-primary openai-pulse"></i>
                        </div>
                        
                        <!-- Status principal -->
                        <h5 id="openai-status-text" class="mb-3">Preparando processamento...</h5>
                        
                        <!-- Barra de progresso -->
                        <div class="progress mb-3" style="height: 25px;">
                            <div id="openai-progress-bar" class="progress-bar progress-bar-striped progress-bar-animated bg-primary" 
                                 role="progressbar" style="width: 0%" aria-valuenow="0" aria-valuemin="0" aria-valuemax="100">
                                <span id="openai-progress-text">0%</span>
                            </div>
                        </div>
                        
                        <!-- Detalhes técnicos -->
                        <div class="alert alert-info" role="alert">
                            <div id="openai-details-text">
                                <strong>OpenAI GPT-4o:</strong> Analisando dados do projeto...
                            </div>
                            <div class="mt-2">
                                <small class="text-muted">
                                    <i class="fas fa-clock me-1"></i>
                                    <span id="openai-timer">00:00</span> | 
                                    <span id="openai-estimation">Estimativa: calculando...</span>
                                </small>
                            </div>
                        </div>
                        
                        <!-- Informações sobre payload -->
                        <div class="row mt-3">
                            <div class="col-md-4">
                                <div class="card border-light">
                                    <div class="card-body text-center p-2">
                                        <i class="fas fa-database text-secondary"></i>
                                        <div class="small mt-1">
                                            <strong id="payload-size">-</strong><br>
                                            <span class="text-muted">Dados</span>
                                        </div>
                                    </div>
                                </div>
                            </div>
                            <div class="col-md-4">
                                <div class="card border-light">
                                    <div class="card-body text-center p-2">
                                        <i class="fas fa-microchip text-secondary"></i>
                                        <div class="small mt-1">
                                            <strong id="token-count">-</strong><br>
                                            <span class="text-muted">Tokens</span>
                                        </div>
                                    </div>
                                </div>
                            </div>
                            <div class="col-md-4">
                                <div class="card border-light">
                                    <div class="card-body text-center p-2">
                                        <i class="fas fa-tachometer-alt text-secondary"></i>
                                        <div class="small mt-1">
                                            <strong id="processing-speed">-</strong><br>
                                            <span class="text-muted">Velocidade</span>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </div>
                        
                        <!-- Aviso sobre payloads grandes -->
                        <div id="payload-warning" class="alert alert-warning mt-3 d-none" role="alert">
                            <i class="fas fa-exclamation-triangle me-2"></i>
                            <strong>Assessment extenso detectado:</strong>
                            <span id="payload-warning-text"></span>
                        </div>
                    </div>
                </div>
            </div>
        </div>
        `;
        
        // Adicionar ao body
        document.body.insertAdjacentHTML('beforeend', modalHTML);
        
        // Inicializar elementos
        this.modal = new bootstrap.Modal(document.getElementById('openaiProcessingModal'), {
            backdrop: 'static',
            keyboard: false
        });
        
        this.progressBar = document.getElementById('openai-progress-bar');
        this.statusText = document.getElementById('openai-status-text');
        this.detailsText = document.getElementById('openai-details-text');
        
        // Adicionar estilos CSS
        this.addStyles();
    }
    
    addStyles() {
        const styles = `
        <style>
        .openai-pulse {
            animation: openai-pulse 2s infinite;
        }
        
        @keyframes openai-pulse {
            0% { opacity: 1; transform: scale(1); }
            50% { opacity: 0.7; transform: scale(1.1); }
            100% { opacity: 1; transform: scale(1); }
        }
        
        .progress-bar-animated {
            animation: progress-bar-stripes 1s linear infinite, openai-glow 2s ease-in-out infinite alternate;
        }
        
        @keyframes openai-glow {
            from { box-shadow: 0 0 5px rgba(13, 110, 253, 0.5); }
            to { box-shadow: 0 0 20px rgba(13, 110, 253, 0.8); }
        }
        
        #openaiProcessingModal .card {
            transition: all 0.3s ease;
        }
        
        #openaiProcessingModal .card:hover {
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        }
        </style>
        `;
        
        document.head.insertAdjacentHTML('beforeend', styles);
    }
    
    show(operation, estimatedDuration = 30) {
        this.currentOperation = operation;
        this.estimatedDuration = estimatedDuration;
        this.startTime = Date.now();
        
        // Configurar textos baseados na operação
        const operations = {
            'introducao': {
                title: 'Gerando Introdução Inteligente',
                details: 'Analisando dados do projeto e gerando introdução técnica personalizada...',
                estimation: '15-30 segundos'
            },
            'analise_dominios': {
                title: 'Analisando Domínios do Assessment',
                details: 'Processando respostas e gerando análises detalhadas por domínio...',
                estimation: '1-3 minutos'
            },
            'consideracoes_finais': {
                title: 'Elaborando Considerações Finais',
                details: 'Consolidando análises e gerando recomendações estratégicas...',
                estimation: '30-60 segundos'
            }
        };
        
        const config = operations[operation] || {
            title: 'Processando com IA',
            details: 'Enviando dados para análise da OpenAI...',
            estimation: '30-60 segundos'
        };
        
        // Atualizar interface
        this.statusText.textContent = config.title;
        this.detailsText.innerHTML = `<strong>OpenAI GPT-4o:</strong> ${config.details}`;
        document.getElementById('openai-estimation').textContent = `Estimativa: ${config.estimation}`;
        
        // Resetar progresso
        this.updateProgress(0);
        
        // Mostrar modal
        this.modal.show();
        
        // Iniciar timer
        this.startTimer();
        
        // Simular progresso inicial
        this.simulateProgress();
    }
    
    updateProgress(percentage, status = null) {
        this.progressBar.style.width = `${percentage}%`;
        this.progressBar.setAttribute('aria-valuenow', percentage);
        document.getElementById('openai-progress-text').textContent = `${Math.round(percentage)}%`;
        
        if (status) {
            this.statusText.textContent = status;
        }
    }
    
    updatePayloadInfo(payloadSize, tokenCount, hasWarning = false, warningText = '') {
        document.getElementById('payload-size').textContent = payloadSize;
        document.getElementById('token-count').textContent = tokenCount;
        
        if (hasWarning) {
            document.getElementById('payload-warning').classList.remove('d-none');
            document.getElementById('payload-warning-text').textContent = warningText;
        }
        
        // Calcular velocidade aproximada
        const elapsed = (Date.now() - this.startTime) / 1000;
        if (elapsed > 0) {
            const speed = Math.round(parseInt(tokenCount.replace(/[^\d]/g, '')) / elapsed);
            document.getElementById('processing-speed').textContent = `${speed} t/s`;
        }
    }
    
    simulateProgress() {
        // Progresso inicial mais rápido
        setTimeout(() => this.updateProgress(15, 'Conectando com OpenAI...'), 500);
        setTimeout(() => this.updateProgress(30, 'Enviando dados...'), 1500);
        setTimeout(() => this.updateProgress(45, 'Processando com IA...'), 3000);
        
        // Progresso mais lento durante processamento real
        let currentProgress = 45;
        const progressInterval = setInterval(() => {
            currentProgress += Math.random() * 5;
            if (currentProgress < 85) {
                this.updateProgress(currentProgress, 'Analisando respostas...');
            } else {
                clearInterval(progressInterval);
            }
        }, 2000);
    }
    
    startTimer() {
        const timerElement = document.getElementById('openai-timer');
        
        const updateTimer = () => {
            const elapsed = Math.floor((Date.now() - this.startTime) / 1000);
            const minutes = Math.floor(elapsed / 60);
            const seconds = elapsed % 60;
            timerElement.textContent = `${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`;
        };
        
        updateTimer();
        this.timerInterval = setInterval(updateTimer, 1000);
    }
    
    hide(success = true, message = '') {
        if (this.timerInterval) {
            clearInterval(this.timerInterval);
        }
        
        if (success) {
            this.updateProgress(100, 'Processamento concluído!');
            
            setTimeout(() => {
                this.modal.hide();
            }, 1500);
        } else {
            this.statusText.textContent = 'Erro no processamento';
            this.detailsText.innerHTML = `<strong>Erro:</strong> ${message}`;
            this.progressBar.classList.remove('bg-primary');
            this.progressBar.classList.add('bg-danger');
            
            setTimeout(() => {
                this.modal.hide();
            }, 3000);
        }
    }
}

// Instância global
window.openaiProcessing = new OpenAIProcessingUI();

// Interceptar cliques em botões OpenAI
document.addEventListener('DOMContentLoaded', function() {
    console.log('OpenAI Processing Interface carregado');
    
    // Interceptar formulários de IA
    const aiFormSelectors = [
        { selector: 'form[action*="gerar_introducao_ia"]', operation: 'introducao' },
        { selector: 'form[action*="gerar_consideracoes_finais"]', operation: 'consideracoes_finais' },
        { selector: 'form[action*="gerar_analise_dominios_ia"]', operation: 'analise_dominios' }
    ];
    
    aiFormSelectors.forEach(({ selector, operation }) => {
        document.addEventListener('submit', function(e) {
            const form = e.target.closest(selector);
            if (form) {
                e.preventDefault();
                console.log(`Interceptando formulário ${operation}`);
                
                const formData = new FormData(form);
                const actionUrl = form.action;
                
                // Mostrar interface de processamento
                window.openaiProcessing.show(operation);
                
                // Fazer requisição
                fetch(actionUrl, { 
                    method: 'POST',
                    body: formData
                })
                .then(response => {
                    if (response.ok) {
                        console.log('Processamento concluído com sucesso');
                        window.openaiProcessing.hide(true);
                        setTimeout(() => window.location.reload(), 2000);
                    } else {
                        throw new Error(`Erro HTTP: ${response.status}`);
                    }
                })
                .catch(error => {
                    console.error('Erro no processamento:', error);
                    window.openaiProcessing.hide(false, error.message);
                    setTimeout(() => window.location.reload(), 3000);
                });
            }
        });
    });
    
    // Também interceptar links diretos (botões de melhoria)
    const aiLinkSelectors = [
        { selector: 'a[href*="gerar_introducao_ia"]', operation: 'introducao' },
        { selector: 'a[href*="gerar_analise_dominios_ia"]', operation: 'analise_dominios' },
        { selector: 'a[href*="gerar_consideracoes_finais"]', operation: 'consideracoes_finais' }
    ];
    
    aiLinkSelectors.forEach(({ selector, operation }) => {
        document.addEventListener('click', function(e) {
            if (e.target.matches(selector) || e.target.closest(selector)) {
                e.preventDefault();
                console.log(`Interceptando link ${operation}`);
                
                const button = e.target.matches(selector) ? e.target : e.target.closest(selector);
                const href = button.href;
                
                // Mostrar interface de processamento
                window.openaiProcessing.show(operation);
                
                // Fazer requisição
                fetch(href, { method: 'POST' })
                    .then(response => {
                        if (response.ok) {
                            console.log('Processamento concluído com sucesso');
                            window.openaiProcessing.hide(true);
                            setTimeout(() => window.location.reload(), 2000);
                        } else {
                            throw new Error(`Erro HTTP: ${response.status}`);
                        }
                    })
                    .catch(error => {
                        console.error('Erro no processamento:', error);
                        window.openaiProcessing.hide(false, error.message);
                        setTimeout(() => window.location.reload(), 3000);
                    });
            }
        });
    });
    
    console.log('Interceptadores configurados para formulários e links de IA');
});