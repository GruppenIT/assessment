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
    
    # Coletar dados para processar em lote
    dominios_para_criar = {}
    perguntas_para_criar = []
    
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
                # Preparar dados do domínio
                nome_dominio = linha['Dominio'].strip()
                if nome_dominio:
                    dominio_key = f"{tipo_assessment_id}:{nome_dominio}"
                    
                    if dominio_key not in dominios_para_criar:
                        dominios_para_criar[dominio_key] = {
                            'nome': nome_dominio,
                            'descricao': linha['DescriçãoDominio'].strip(),
                            'ordem': linha['OrdemDominio'].strip(),
                            'perguntas': []
                        }
                    
                    # Preparar dados da pergunta
                    texto_pergunta = linha['Pergunta'].strip()
                    if texto_pergunta:
                        if len(texto_pergunta) > 1000:
                            texto_pergunta = texto_pergunta[:1000]
                        
                        dominios_para_criar[dominio_key]['perguntas'].append({
                            'texto': texto_pergunta,
                            'descricao': linha['DescriçãoPergunta'].strip(),
                            'ordem': linha['OrdemPergunta'].strip()
                        })
                
            except Exception as e:
                resultado['erros'].append(f'Erro na linha {linha_num}: {str(e)}')
        
        # Processar domínios e perguntas em lote
        if not resultado['erros']:
            try:
                for dominio_key, dominio_data in dominios_para_criar.items():
                    # Verificar se domínio já existe
                    nome_dominio = dominio_data['nome']
                    dominio_existente = Dominio.query.filter_by(
                        tipo_assessment_id=tipo_assessment_id,
                        nome=nome_dominio
                    ).first()
                    
                    if dominio_existente:
                        resultado['dominios_existentes'] += 1
                        dominio_obj = dominio_existente
                    else:
                        # Criar novo domínio
                        try:
                            ordem = int(dominio_data['ordem']) if dominio_data['ordem'] else 1
                        except ValueError:
                            ordem = 1
                        
                        nome_normalizado = nome_dominio.encode('utf-8', errors='ignore').decode('utf-8')
                        descricao_normalizada = dominio_data['descricao'].encode('utf-8', errors='ignore').decode('utf-8') if dominio_data['descricao'] else None
                        
                        dominio_obj = Dominio(
                            tipo_assessment_id=tipo_assessment_id,
                            nome=nome_normalizado[:100],
                            descricao=descricao_normalizada[:500] if descricao_normalizada else None,
                            ordem=ordem,
                            ativo=True
                        )
                        db.session.add(dominio_obj)
                        resultado['dominios_criados'] += 1
                    
                    # Processar perguntas do domínio
                    for pergunta_data in dominio_data['perguntas']:
                        texto_pergunta = pergunta_data['texto']
                        
                        # Verificar se pergunta já existe
                        pergunta_existente = None
                        if dominio_obj.id:
                            pergunta_existente = Pergunta.query.filter_by(
                                dominio_id=dominio_obj.id,
                                texto=texto_pergunta
                            ).first()
                        
                        if pergunta_existente:
                            resultado['perguntas_existentes'] += 1
                        else:
                            # Criar nova pergunta
                            try:
                                ordem = int(pergunta_data['ordem']) if pergunta_data['ordem'] else 1
                            except ValueError:
                                ordem = 1
                            
                            texto_normalizado = texto_pergunta.encode('utf-8', errors='ignore').decode('utf-8')
                            descricao_normalizada = pergunta_data['descricao'].encode('utf-8', errors='ignore').decode('utf-8') if pergunta_data['descricao'] else None
                            
                            pergunta_obj = Pergunta(
                                dominio=dominio_obj,
                                texto=texto_normalizado[:1000],
                                descricao=descricao_normalizada[:1000] if descricao_normalizada else None,
                                ordem=ordem,
                                ativo=True
                            )
                            db.session.add(pergunta_obj)
                            resultado['perguntas_criadas'] += 1
                
                # Commit único no final
                db.session.commit()
                resultado['sucesso'] = True
                
            except Exception as e:
                db.session.rollback()
                resultado['erros'].append(f'Erro ao salvar no banco: {str(e)}')
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
    try:
        dominio_existente = Dominio.query.filter_by(
            tipo_assessment_id=tipo_assessment_id,
            nome=nome
        ).first()
    except Exception as e:
        # Se der erro na query, assumir que não existe e continuar
        dominio_existente = None
    
    if dominio_existente:
        return {'criado': False, 'objeto': dominio_existente}
    
    # Processar ordem
    try:
        ordem = int(ordem_str) if ordem_str else 1
    except ValueError:
        ordem = 1
    
    # Criar novo domínio
    # Limitar tamanhos dos campos e normalizar encoding
    nome_truncado = nome[:100] if len(nome) > 100 else nome
    descricao_truncada = descricao[:500] if descricao and len(descricao) > 500 else descricao
    
    # Normalizar caracteres especiais
    nome_normalizado = nome_truncado.encode('utf-8', errors='ignore').decode('utf-8')
    descricao_normalizada = descricao_truncada.encode('utf-8', errors='ignore').decode('utf-8') if descricao_truncada else None
    
    novo_dominio = Dominio(
        tipo_assessment_id=tipo_assessment_id,
        nome=nome_normalizado,
        descricao=descricao_normalizada,
        ordem=ordem,
        ativo=True
    )
    
    try:
        db.session.add(novo_dominio)
        db.session.flush()  # Para obter o ID
        return {'criado': True, 'objeto': novo_dominio}
    except Exception as e:
        # Em caso de erro, fazer rollback e retornar erro
        db.session.rollback()
        raise Exception(f'Erro ao criar domínio: {str(e)}')

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
    try:
        pergunta_existente = Pergunta.query.filter_by(
            dominio_id=dominio_id,
            texto=texto
        ).first()
    except Exception as e:
        # Se der erro na query, assumir que não existe e continuar
        pergunta_existente = None
    
    if pergunta_existente:
        return {'criado': False, 'objeto': pergunta_existente}
    
    # Processar ordem
    try:
        ordem = int(ordem_str) if ordem_str else 1
    except ValueError:
        ordem = 1
    
    # Criar nova pergunta
    # Limitar tamanhos dos campos e normalizar encoding
    texto_truncado = texto[:1000] if len(texto) > 1000 else texto
    descricao_truncada = descricao[:1000] if descricao and len(descricao) > 1000 else descricao
    
    # Normalizar caracteres especiais
    texto_normalizado = texto_truncado.encode('utf-8', errors='ignore').decode('utf-8')
    descricao_normalizada = descricao_truncada.encode('utf-8', errors='ignore').decode('utf-8') if descricao_truncada else None
    
    nova_pergunta = Pergunta(
        dominio_id=dominio_id,
        texto=texto_normalizado,
        descricao=descricao_normalizada,
        ordem=ordem,
        ativo=True
    )
    
    try:
        db.session.add(nova_pergunta)
        db.session.flush()  # Para obter o ID
        return {'criado': True, 'objeto': nova_pergunta}
    except Exception as e:
        # Em caso de erro, fazer rollback e retornar erro
        db.session.rollback()
        raise Exception(f'Erro ao criar pergunta: {str(e)}')

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