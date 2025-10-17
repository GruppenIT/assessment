# Sistema de Grupos para Assessments Públicos

## 📊 Visão Geral

Sistema de agrupamento e análise comparativa de assessments públicos, permitindo segmentação por campanhas, turmas, departamentos ou qualquer critério personalizado.

## 🚀 Como Funciona

### 1. Criação de Grupos Automática

Os grupos são criados automaticamente quando um assessment público é acessado com o parâmetro `?group=` na URL:

```
https://seu-dominio.com/public/1?group=turma2024
https://seu-dominio.com/public/1?group=departamento_ti
https://seu-dominio.com/public/1?group=campanha_seguranca
```

### 2. Fluxo de Uso

1. **Compartilhe o link** com o parâmetro de grupo
2. **Usuários respondem** o assessment normalmente
3. **Sistema salva automaticamente** o grupo no registro
4. **Acesse `/public/grupos`** para ver todos os grupos
5. **Clique no grupo** para ver dashboard com estatísticas médias

### 3. Rotas Disponíveis

#### Listagem de Grupos
```
GET /public/grupos
```
Exibe todos os grupos com:
- Nome do grupo
- Total de assessments respondidos
- Tipo de assessment

#### Dashboard do Grupo
```
GET /public/grupos/<nome_grupo>
```
Exibe estatísticas detalhadas:
- Pontuação média geral do grupo
- Gráfico de barras com médias por domínio
- Lista detalhada com variação (mín-máx) de cada domínio
- Total de respostas por domínio

## 📈 Análises Disponíveis

### Dashboard do Grupo Inclui:

1. **Métricas Gerais**
   - Pontuação média geral (0-100%)
   - Total de assessments respondidos

2. **Gráfico Interativo (Chart.js)**
   - Barras horizontais com médias por domínio
   - Tooltips com informações detalhadas
   - Design responsivo

3. **Detalhamento por Domínio**
   - Nome do domínio
   - Média de pontuação
   - Variação (pontuação mínima e máxima)
   - Total de respostas computadas

## 💡 Casos de Uso

### 1. Educação
```
/public/1?group=turma_2024_1
/public/1?group=turma_2024_2
```
Compare o desempenho médio entre turmas diferentes

### 2. Departamentos
```
/public/1?group=depto_ti
/public/1?group=depto_financeiro
/public/1?group=depto_rh
```
Identifique áreas que precisam de mais atenção

### 3. Campanhas de Marketing
```
/public/1?group=campanha_email_jan
/public/1?group=campanha_social_jan
```
Meça a efetividade de diferentes canais de divulgação

### 4. Filiais/Unidades
```
/public/1?group=filial_sp
/public/1?group=filial_rj
```
Compare maturidade entre diferentes unidades de negócio

## 🎨 Design

- **Interface moderna** com gradientes e sombras
- **Cards interativos** com hover effects
- **Gráficos responsivos** usando Chart.js
- **Design mobile-first** totalmente responsivo
- **Branding corporativo** com logos das empresas

## 🔧 Implementação Técnica

### Modelo de Dados
```python
class AssessmentPublico(db.Model):
    # ... outros campos
    grupo = db.Column(db.String(100), comment='Grupo do assessment')
```

### Captura do Parâmetro
```python
# Rota inicial captura ?group= da URL
grupo = request.args.get('group')
assessment_publico = AssessmentPublico(
    # ... outros campos
    grupo=grupo
)
```

### Cálculo de Médias
```python
# Agrupa assessments por grupo
# Calcula média de pontuação por domínio
# Exibe estatísticas comparativas
```

## 📊 Migração de Banco de Dados

A coluna `grupo` foi adicionada à tabela `assessments_publicos`:

```sql
ALTER TABLE assessments_publicos 
ADD COLUMN IF NOT EXISTS grupo VARCHAR(100);
```

## 🎯 Próximos Passos Sugeridos

1. **Exportação de Dados**: Permitir download CSV/Excel das estatísticas
2. **Filtros Avançados**: Filtrar por período, tipo de assessment
3. **Comparação Visual**: Gráficos de comparação lado a lado
4. **Alertas**: Notificações quando grupo atingir determinado número de respostas
5. **API REST**: Endpoints para integração com outros sistemas

## 🔗 URLs de Exemplo

### Desenvolvimento (Replit)
```
https://[seu-repl].replit.dev/public/grupos
https://[seu-repl].replit.dev/public/grupos/turma2024
```

### Produção (On-Premise)
```
https://assessments.zerobox.com.br/public/grupos
https://assessments.zerobox.com.br/public/grupos/turma2024
```

## ✅ Checklist de Teste

- [ ] Acessar assessment com `?group=teste`
- [ ] Responder todas as perguntas
- [ ] Verificar que grupo foi salvo no banco
- [ ] Acessar `/public/grupos` e ver grupo listado
- [ ] Clicar no grupo e visualizar dashboard
- [ ] Verificar gráficos e estatísticas
- [ ] Testar responsividade no mobile

## 📝 Notas Importantes

- Apenas assessments **concluídos** (com `data_conclusao`) aparecem nas estatísticas
- O nome do grupo é **case-sensitive** (turma2024 ≠ Turma2024)
- Grupos vazios (sem assessments concluídos) não aparecem na listagem
- Estatísticas são calculadas em tempo real (sem cache)
