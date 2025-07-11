import csv
import io
from app import db
from models.tipo_assessment import TipoAssessment
from models.dominio import Dominio
from models.pergunta import Pergunta

def processar_csv_importacao(arquivo_csv, tipo_assessment_id):
    """
    Processa um arquivo CSV para importação de domínios e perguntas
    
    Formato esperado do CSV (separador: ponto-e-vírgula):
    Tipo;Dominio;DescriçãoDominio;OrdemDominio;Pergunta;DescriçãoPergunta;OrdemPergunta
    
    Args:
        arquivo_csv: Arquivo CSV enviado via form
        tipo_assessment_id: ID do tipo de assessment
    
    Returns:
        dict: Resultado da importação com estatísticas
    """
    resultado = {
        'sucesso': False,
        'dominios_criados': 0,
        'dominios_existentes': 0,
        'perguntas_criadas': 0,
        'perguntas_existentes': 0,
        'erros': []
    }
    
    try:
        # Verificar se o tipo de assessment existe
        tipo_assessment = TipoAssessment.query.get(tipo_assessment_id)
        if not tipo_assessment:
            resultado['erros'].append('Tipo de assessment não encontrado')
            return resultado
        
        # Ler o arquivo CSV usando ponto-e-vírgula como separador
        arquivo_bytes = arquivo_csv.read()
        
        # Tentar diferentes encodings
        for encoding in ['utf-8-sig', 'utf-8', 'latin-1', 'cp1252']:
            try:
                conteudo = arquivo_bytes.decode(encoding)
                break
            except UnicodeDecodeError:
                continue
        else:
            resultado['erros'].append('Não foi possível decodificar o arquivo. Verifique a codificação.')
            return resultado
        
        stream = io.StringIO(conteudo)
        csv_reader = csv.DictReader(stream, delimiter=';')
        
        # Debug: mostrar fieldnames encontrados
        fieldnames_encontrados = csv_reader.fieldnames or []
        
        # Verificar cabeçalhos esperados
        colunas_esperadas = ['Tipo', 'Dominio', 'DescriçãoDominio', 'OrdemDominio', 
                           'Pergunta', 'DescriçãoPergunta', 'OrdemPergunta']
        
        # Limpar possíveis espaços nos fieldnames
        if fieldnames_encontrados:
            fieldnames_limpos = [field.strip() for field in fieldnames_encontrados]
            csv_reader.fieldnames = fieldnames_limpos
        
        if not all(col in fieldnames_limpos for col in colunas_esperadas):
            resultado['erros'].append(f'CSV deve conter as colunas: {", ".join(colunas_esperadas)}. Encontradas: {", ".join(fieldnames_limpos)}')
            return resultado
        
        linha_num = 1
        for linha in csv_reader:
            linha_num += 1
            
            try:
                # Processar domínio
                nome_dominio = linha['Dominio'].strip()
                if nome_dominio:
                    dominio = processar_dominio(
                        tipo_assessment_id,
                        nome_dominio,
                        linha['DescriçãoDominio'].strip(),
                        linha['OrdemDominio'].strip()
                    )
                    
                    if dominio['criado']:
                        resultado['dominios_criados'] += 1
                    else:
                        resultado['dominios_existentes'] += 1
                    
                    # Processar pergunta
                    texto_pergunta = linha['Pergunta'].strip()
                    if texto_pergunta:
                        pergunta = processar_pergunta(
                            dominio['objeto'].id,
                            texto_pergunta,
                            linha['DescriçãoPergunta'].strip(),
                            linha['OrdemPergunta'].strip()
                        )
                        
                        if pergunta['criado']:
                            resultado['perguntas_criadas'] += 1
                        else:
                            resultado['perguntas_existentes'] += 1
                
            except Exception as e:
                resultado['erros'].append(f'Erro na linha {linha_num}: {str(e)}')
        
        # Commit das alterações se não houver erros críticos
        if not resultado['erros']:
            db.session.commit()
            resultado['sucesso'] = True
        else:
            db.session.rollback()
            
    except Exception as e:
        db.session.rollback()
        resultado['erros'].append(f'Erro ao processar arquivo: {str(e)}')
    
    return resultado

def processar_dominio(tipo_assessment_id, nome, descricao, ordem_str):
    """
    Processa um domínio individual
    
    Args:
        tipo_assessment_id: ID do tipo de assessment
        nome: Nome do domínio
        descricao: Descrição do domínio
        ordem_str: Ordem como string
    
    Returns:
        dict: Resultado do processamento
    """
    # Verificar se já existe
    dominio_existente = Dominio.query.filter_by(
        tipo_assessment_id=tipo_assessment_id,
        nome=nome
    ).first()
    
    if dominio_existente:
        return {'criado': False, 'objeto': dominio_existente}
    
    # Processar ordem
    try:
        ordem = int(ordem_str) if ordem_str else 1
    except ValueError:
        ordem = 1
    
    # Criar novo domínio
    novo_dominio = Dominio(
        tipo_assessment_id=tipo_assessment_id,
        nome=nome,
        descricao=descricao if descricao else None,
        ordem=ordem,
        ativo=True
    )
    
    db.session.add(novo_dominio)
    db.session.flush()  # Para obter o ID
    
    return {'criado': True, 'objeto': novo_dominio}

def processar_pergunta(dominio_id, texto, descricao, ordem_str):
    """
    Processa uma pergunta individual
    
    Args:
        dominio_id: ID do domínio
        texto: Texto da pergunta
        descricao: Descrição da pergunta
        ordem_str: Ordem como string
    
    Returns:
        dict: Resultado do processamento
    """
    # Verificar se já existe (mesmo texto no mesmo domínio)
    pergunta_existente = Pergunta.query.filter_by(
        dominio_id=dominio_id,
        texto=texto
    ).first()
    
    if pergunta_existente:
        return {'criado': False, 'objeto': pergunta_existente}
    
    # Processar ordem
    try:
        ordem = int(ordem_str) if ordem_str else 1
    except ValueError:
        ordem = 1
    
    # Criar nova pergunta
    nova_pergunta = Pergunta(
        dominio_id=dominio_id,
        texto=texto,
        descricao=descricao if descricao else None,
        ordem=ordem,
        ativo=True
    )
    
    db.session.add(nova_pergunta)
    db.session.flush()  # Para obter o ID
    
    return {'criado': True, 'objeto': nova_pergunta}

def gerar_template_csv():
    """
    Gera um template CSV de exemplo
    
    Returns:
        str: Conteúdo do CSV template
    """
    template_data = [
        {
            'Tipo': 'Cibersegurança',
            'Dominio': 'Governança e Gestão de Riscos',
            'DescriçãoDominio': 'Políticas, procedimentos e governança de segurança',
            'OrdemDominio': '1',
            'Pergunta': 'A organização possui uma política de segurança da informação formal e atualizada?',
            'DescriçãoPergunta': 'Verificar se existe documentação formal das políticas de segurança',
            'OrdemPergunta': '1'
        },
        {
            'Tipo': 'Cibersegurança',
            'Dominio': 'Governança e Gestão de Riscos',
            'DescriçãoDominio': 'Políticas, procedimentos e governança de segurança',
            'OrdemDominio': '1',
            'Pergunta': 'Existe um processo formal de gestão de riscos de segurança?',
            'DescriçãoPergunta': 'Avaliar se há metodologia estruturada para identificação e gestão de riscos',
            'OrdemPergunta': '2'
        },
        {
            'Tipo': 'Cibersegurança',
            'Dominio': 'Controles de Acesso',
            'DescriçãoDominio': 'Gestão de identidades e controle de acesso',
            'OrdemDominio': '2',
            'Pergunta': 'A organização implementa autenticação multifator para sistemas críticos?',
            'DescriçãoPergunta': 'Verificar se há controles adicionais de autenticação implementados',
            'OrdemPergunta': '1'
        }
    ]
    
    output = io.StringIO()
    fieldnames = ['Tipo', 'Dominio', 'DescriçãoDominio', 'OrdemDominio', 
                  'Pergunta', 'DescriçãoPergunta', 'OrdemPergunta']
    
    writer = csv.DictWriter(output, fieldnames=fieldnames, delimiter=';')
    writer.writeheader()
    writer.writerows(template_data)
    
    return output.getvalue()