# Sistema de Avaliações de Maturidade - Guia Rápido On-Premise

## 📋 Arquivos de Implantação

### Documentação
- **`IMPLANTACAO-ONPREMISE.md`** - Documentação completa de instalação

### Scripts de Instalação e Manutenção
- **`instalar_sistema.py`** - Instala o sistema completo
- **`verificar_instalacao.py`** - Verifica se tudo está funcionando
- **`atualizar_sistema.sh`** - Atualiza o sistema
- **`migrar_banco.py`** - Executa migrações do banco

### Arquivo de Configuração Essencial
- **`env_loader.py`** - Carrega variáveis de ambiente automaticamente

## 🚀 Instalação Rápida

1. **Preparar servidor Ubuntu**
2. **Seguir guia**: `IMPLANTACAO-ONPREMISE.md`
3. **Executar**: `python3 instalar_sistema.py`
4. **Verificar**: `python3 verificar_instalacao.py`

## 🔧 Manutenção

- **Atualizar sistema**: `bash atualizar_sistema.sh`
- **Migrar banco**: `python3 migrar_banco.py`
- **Verificar status**: `python3 verificar_instalacao.py`

## 📞 Suporte

Consulte `IMPLANTACAO-ONPREMISE.md` para informações detalhadas sobre:
- Pré-requisitos
- Configuração do PostgreSQL
- Configuração do Nginx
- Solução de problemas
- Logs e monitoramento

---
**Versão**: 2.1 | **Data**: $(date +%d/%m/%Y)