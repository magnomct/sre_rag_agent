#!/usr/bin/env python3
# ==============================================================================
# SRE RAG Agent v3.5 — Gerador Oficial do tests.pdf
# Produz o Guia de Execução Local em PDF com ReportLab (3 páginas balanceadas)
# ==============================================================================

import os
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    PageBreak,
    KeepTogether,
)
from reportlab.pdfgen import canvas


class NumberedCanvas(canvas.Canvas):
    """Canvas de dois passos para calcular dinamicamente 'Página X de Y'."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_decorations(num_pages)
            super().showPage()
        super().save()

    def draw_page_decorations(self, page_count):
        self.saveState()
        self.setStrokeColor(colors.HexColor("#d0d7de"))
        self.setFillColor(colors.HexColor("#6e7781"))
        self.setLineWidth(0.5)
        self.setFont("Helvetica", 8.5)

        # Header (topo: y=755 linha, y=762 texto)
        self.line(40, 755, 572, 755)
        self.drawString(40, 762, "SRE RAG Agent v3.5 — Guia de Execução Local (Step by Step)")

        # Footer (rodapé: y=42 linha, y=30 texto)
        self.line(40, 42, 572, 42)
        self.drawString(40, 30, "SRE Incident Simulation Lab · Carlos Magno Cordeiro © 2026")
        page_str = f"Página {self._pageNumber} de {page_count}"
        self.drawRightString(572, 30, page_str)

        self.restoreState()


def create_section_header(title, badge_text, badge_color_hex="#1a7f37"):
    """Cria a barra visual de título de seção com badge."""
    text = f"""
    <font face="Helvetica-Bold" size="11" color="#1f2328"><b>{title}</b></font>
    &nbsp;&nbsp;&nbsp;&nbsp;
    <font face="Helvetica-Bold" size="9.5" color="{badge_color_hex}"><b>[{badge_text}]</b></font>
    """
    p = Paragraph(text.strip(), ParagraphStyle("SecHead", leading=14))
    t = Table([[p]], colWidths=[532])
    t.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#f0f4f9")),
                ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#d0d7de")),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                ("LEFTPADDING", (0, 0), (-1, -1), 8),
                ("RIGHTPADDING", (0, 0), (-1, -1), 8),
            ]
        )
    )
    return t


def create_code_block(code_lines):
    """Cria um bloco estilizado de código monospaçado."""
    formatted_lines = []
    for line in code_lines:
        line_clean = line.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        if line_clean.strip().startswith("#"):
            formatted_lines.append(f'<font color="#6e7781"><i>{line_clean}</i></font>')
        else:
            formatted_lines.append(f'<font color="#0969da">{line_clean}</font>')
    content = "<br/>".join(formatted_lines)
    p = Paragraph(content, ParagraphStyle("CodeP", fontName="Courier", fontSize=8.2, leading=11.2))
    t = Table([[p]], colWidths=[532])
    t.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#f6f8fa")),
                ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#d0d7de")),
                ("TOPPADDING", (0, 0), (-1, -1), 3.5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 3.5),
                ("LEFTPADDING", (0, 0), (-1, -1), 7),
                ("RIGHTPADDING", (0, 0), (-1, -1), 7),
            ]
        )
    )
    return t


def build_pdf(filename="/home/magno/sre_rag_agent/tests.pdf"):
    doc = SimpleDocTemplate(
        filename,
        pagesize=letter,
        leftMargin=40,
        rightMargin=40,
        topMargin=42,
        bottomMargin=46,
    )

    doc_title_style = ParagraphStyle(
        "DocTitle",
        fontName="Helvetica-Bold",
        fontSize=18,
        leading=22,
        textColor=colors.HexColor("#0969da"),
    )

    doc_subtitle_style = ParagraphStyle(
        "DocSubTitle",
        fontName="Helvetica",
        fontSize=9.8,
        leading=13,
        textColor=colors.HexColor("#57606a"),
    )

    body_style = ParagraphStyle(
        "DocBody",
        fontName="Helvetica",
        fontSize=8.8,
        leading=12,
        textColor=colors.HexColor("#24292f"),
    )

    sec_desc_style = ParagraphStyle(
        "SecDesc",
        fontName="Helvetica-Oblique",
        fontSize=8.4,
        leading=11.5,
        textColor=colors.HexColor("#57606a"),
    )

    step_title_style = ParagraphStyle(
        "StepTitle",
        fontName="Helvetica-Bold",
        fontSize=9.2,
        leading=12.5,
        textColor=colors.HexColor("#24292f"),
    )

    table_header_style = ParagraphStyle(
        "TH",
        fontName="Helvetica-Bold",
        fontSize=8.2,
        leading=10.5,
        textColor=colors.HexColor("#24292f"),
    )

    table_cell_style = ParagraphStyle(
        "TD",
        fontName="Helvetica",
        fontSize=8.2,
        leading=10.5,
        textColor=colors.HexColor("#24292f"),
    )

    table_url_style = ParagraphStyle(
        "TD_URL",
        fontName="Helvetica",
        fontSize=8.2,
        leading=10.5,
        textColor=colors.HexColor("#0969da"),
    )

    story = []

    # =========================================================================
    # PÁGINA 1 — Header do Documento + Novidades v3.5 + Opção 1 (Dev Local)
    # =========================================================================

    story.append(Spacer(1, 4))
    story.append(Paragraph("■ SRE RAG Agent v3.5 — Guia de Execução Local", doc_title_style))
    story.append(Spacer(1, 2))
    story.append(
        Paragraph("Passo a Passo (Step by Step) para Inicialização, Operação e Validação do Laboratório", doc_subtitle_style)
    )
    story.append(Spacer(1, 5))

    intro_text = (
        "Este documento reúne as 3 formas homologadas de subir e operar o ambiente do "
        "<b>SRE Incident Simulation Lab v3.5</b> em ambiente local (WSL2 / Ubuntu ou Linux). "
        "Escolha a opção mais adequada ao seu objetivo de estudo ou teste."
    )
    story.append(Paragraph(intro_text, body_style))
    story.append(Spacer(1, 6))

    # Box de Destaques da v3.5 (Novidades & Hardening)
    v34_highlights_html = (
        "<b>🛡️ Novidades &amp; Hardening da v3.5:</b> "
        "• <b>Pydantic V2 ConfigDict:</b> Zero DeprecationWarnings no bootstrap de configs.<br/>"
        "• <b>Health Check TTL Cache (5s):</b> Prevenção contra connection storms e medição de latência real de DB/Redis.<br/>"
        "• <b>Async Embeddings:</b> <i>asyncio.to_thread</i> na inferência vetorial, liberando o event loop do FastAPI.<br/>"
        "• <b>GZip &amp; Nginx Cache:</b> Compressão transparente &gt;1KB e cache estático (expires 1h) para assets imutáveis.<br/>"
        "• <b>Defesa em Profundidade:</b> Security Headers automáticos (CSP, HSTS, XFO) e Rate Limiter (30 req/min no RAG)."
    )
    v34_box_p = Paragraph(v34_highlights_html, ParagraphStyle("V34Box", fontName="Helvetica", fontSize=8.0, leading=11, textColor=colors.HexColor("#1f2328")))
    v34_box = Table([[v34_box_p]], colWidths=[532])
    v34_box.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#f0f8ff")),
                ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#54aeff")),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                ("LEFTPADDING", (0, 0), (-1, -1), 7),
                ("RIGHTPADDING", (0, 0), (-1, -1), 7),
            ]
        )
    )
    story.append(v34_box)
    story.append(Spacer(1, 8))

    # Opção 1: Dev Local Rápido
    story.append(create_section_header("Opção 1: Modo Desenvolvimento Local Rápido", "MAIS RÁPIDO", "#1a7f37"))
    story.append(Spacer(1, 4))
    story.append(
        Paragraph(
            "Ideal para desenvolvimento, testes de UI, simulação de incidentes e uso do War Room sem necessidade de inicializar contêineres Docker.",
            sec_desc_style,
        )
    )
    story.append(Spacer(1, 5))

    # Passo 1
    story.append(Paragraph("Passo 1: Navegue até o diretório raiz do projeto:", step_title_style))
    story.append(Spacer(1, 2))
    story.append(create_code_block(["cd /home/magno/sre_rag_agent"]))
    story.append(Spacer(1, 4))

    # Passo 2
    story.append(Paragraph("Passo 2: Crie e ative o ambiente virtual Python 3.12 (caso ainda não exista):", step_title_style))
    story.append(Spacer(1, 2))
    story.append(create_code_block(["python3 -m venv app/.venv", "source app/.venv/bin/activate"]))
    story.append(Spacer(1, 4))

    # Passo 3
    story.append(Paragraph("Passo 3: Instale as dependências (com PyTorch CPU otimizado, sem CUDA bloat):", step_title_style))
    story.append(Spacer(1, 2))
    story.append(
        create_code_block(
            [
                "pip install --upgrade pip",
                "pip install torch --index-url https://download.pytorch.org/whl/cpu",
                "pip install -r app/requirements.txt",
            ]
        )
    )
    story.append(Spacer(1, 4))

    # Passo 4
    story.append(Paragraph("Passo 4: Inicie o servidor ASGI (Uvicorn) na porta 8080:", step_title_style))
    story.append(Spacer(1, 2))
    story.append(
        create_code_block(
            [
                "cd app",
                "../app/.venv/bin/uvicorn main:app --host 0.0.0.0 --port 8080 --reload",
                "# Ou execute diretamente na raiz: make dev",
            ]
        )
    )
    story.append(Spacer(1, 4))

    # Passo 5: Tabela de Endpoints
    story.append(Paragraph("Passo 5: Acesse a interface e endpoints no navegador:", step_title_style))
    story.append(Spacer(1, 3))

    table_data = [
        [
            Paragraph("Dashboard Principal & Quiz", table_header_style),
            Paragraph("http://localhost:8080/dashboard", table_url_style),
            Paragraph("Simulador de incidentes, vitrine e runbooks em 5 fases", table_cell_style),
        ],
        [
            Paragraph("War Room (Terminal Interativo)", table_header_style),
            Paragraph("http://localhost:8080/dashboard#warroom", table_url_style),
            Paragraph("Terminal CLI seguro com comandos simulados (kubectl/helm)", table_cell_style),
        ],
        [
            Paragraph("Conceitos SRE & Arquitetura", table_header_style),
            Paragraph("http://localhost:8080/dashboard#concepts", table_url_style),
            Paragraph("Hub pedagógico de baixo nível (cgroups, CFS, epoll, probes)", table_cell_style),
        ],
        [
            Paragraph("Métricas & Histórico", table_header_style),
            Paragraph("http://localhost:8080/dashboard#history", table_url_style),
            Paragraph("Histórico de simulações, acertos e métricas de desempenho", table_cell_style),
        ],
        [
            Paragraph("Health Check da Aplicação", table_header_style),
            Paragraph("http://localhost:8080/healthz", table_url_style),
            Paragraph("Health check com cache TTL 5s e latência real do banco (v3.5)", table_cell_style),
        ],
        [
            Paragraph("Métricas Prometheus (RED)", table_header_style),
            Paragraph("http://localhost:8080/metrics", table_url_style),
            Paragraph("Métricas de Rate, Errors e Duration prontas para scraping", table_cell_style),
        ],
    ]

    t_endpoints = Table(table_data, colWidths=[150, 195, 187])
    t_endpoints.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#ffffff")),
                ("ROWBACKGROUNDS", (0, 0), (-1, -1), [colors.HexColor("#ffffff"), colors.HexColor("#f8fafc")]),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#d0d7de")),
                ("TOPPADDING", (0, 0), (-1, -1), 3),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
                ("LEFTPADDING", (0, 0), (-1, -1), 6),
                ("RIGHTPADDING", (0, 0), (-1, -1), 6),
            ]
        )
    )
    story.append(t_endpoints)

    # =========================================================================
    # PÁGINA 2 — Opção 2 (Docker Compose) + Opção 3 (Kubernetes Kind + Helm)
    # =========================================================================
    story.append(PageBreak())
    story.append(Spacer(1, 4))

    # Opção 2: Docker Compose
    story.append(create_section_header("Opção 2: Modo Docker Compose (Multi-Network Isolado)", "STACK SEGURA", "#0969da"))
    story.append(Spacer(1, 4))
    story.append(
        Paragraph(
            "Sobe o ecossistema completo em contêineres: Nginx (Proxy reverso público na porta 80 com compressão GZip e cache), "
            "FastAPI (API), PostgreSQL e Redis interligados pela rede interna isolada <i>backend_net</i>.",
            sec_desc_style,
        )
    )
    story.append(Spacer(1, 5))

    story.append(Paragraph("Passo 1: Execute o build e inicialize os serviços em background:", step_title_style))
    story.append(Spacer(1, 2))
    story.append(
        create_code_block(
            [
                "cd /home/magno/sre_rag_agent",
                "docker compose up -d --build",
                "# Ou use o atalho homologado: make compose-up",
            ]
        )
    )
    story.append(Spacer(1, 4))

    story.append(Paragraph("Passo 2: Verifique a saúde e o status de inicialização dos contêineres:", step_title_style))
    story.append(Spacer(1, 2))
    story.append(create_code_block(["docker compose ps"]))
    story.append(Spacer(1, 4))

    story.append(Paragraph("Passo 3: Acesso aos serviços via Nginx Reverse Proxy (Porta 80):", step_title_style))
    story.append(Spacer(1, 2))

    t_compose = Table(
        [
            [Paragraph("Interface Web Principal", table_header_style), Paragraph("http://localhost/dashboard", table_url_style), Paragraph("Porta 80 padrão com GZip ativo", table_cell_style)],
            [Paragraph("Métricas Prometheus", table_header_style), Paragraph("http://localhost/metrics", table_url_style), Paragraph("Coleta RED para scrape", table_cell_style)],
            [Paragraph("Health Check Nginx/API", table_header_style), Paragraph("http://localhost/healthz", table_url_style), Paragraph("Status com cache defensivo", table_cell_style)],
        ],
        colWidths=[150, 195, 187],
    )
    t_compose.setStyle(
        TableStyle(
            [
                ("ROWBACKGROUNDS", (0, 0), (-1, -1), [colors.HexColor("#ffffff"), colors.HexColor("#f8fafc")]),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#d0d7de")),
                ("TOPPADDING", (0, 0), (-1, -1), 3),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
                ("LEFTPADDING", (0, 0), (-1, -1), 6),
                ("RIGHTPADDING", (0, 0), (-1, -1), 6),
            ]
        )
    )
    story.append(t_compose)
    story.append(Spacer(1, 4))

    story.append(Paragraph("Passo 4: Encerrar a stack quando finalizar os testes:", step_title_style))
    story.append(Spacer(1, 2))
    story.append(
        create_code_block(
            [
                "docker compose down",
                "# Ou use o atalho homologado: make compose-down",
            ]
        )
    )
    story.append(Spacer(1, 7))

    # Opção 3: Modo Cluster Kubernetes (Kind + Helm)
    story.append(create_section_header("Opção 3: Modo Cluster Kubernetes (Kind + Helm)", "PRODUÇÃO REAL", "#8250df"))
    story.append(Spacer(1, 4))
    story.append(
        Paragraph(
            "Simulação completa de cluster K8s local com orquestração Helm (Chart v0.2.0, appVersion 3.5), "
            "Prometheus Operator, Alertmanager e dashboards Grafana pré-configurados.",
            sec_desc_style,
        )
    )
    story.append(Spacer(1, 5))

    story.append(Paragraph("Passo 1: Provisionar o cluster Kind e a stack de monitoramento:", step_title_style))
    story.append(Spacer(1, 2))
    story.append(create_code_block(["cd /home/magno/sre_rag_agent", "make setup"]))
    story.append(Spacer(1, 4))

    story.append(Paragraph("Passo 2: Realizar o deploy do SRE RAG Agent via Helm (v3.5):", step_title_style))
    story.append(Spacer(1, 2))
    story.append(create_code_block(["make deploy"]))
    story.append(Spacer(1, 4))

    story.append(Paragraph("Passo 3: Iniciar o encaminhamento de portas (Port-Forward):", step_title_style))
    story.append(Spacer(1, 2))
    story.append(create_code_block(["make port-forward"]))
    story.append(Spacer(1, 4))

    story.append(Paragraph("Passo 4: Painéis e Credenciais de Acesso ao Cluster:", step_title_style))
    story.append(Spacer(1, 2))

    t_k8s = Table(
        [
            [Paragraph("Aplicação SRE RAG", table_header_style), Paragraph("http://localhost:8080/dashboard", table_url_style), Paragraph("Sem autenticação (Ambiente de Lab)", table_cell_style)],
            [Paragraph("Prometheus", table_header_style), Paragraph("http://localhost:9090", table_url_style), Paragraph("Métricas PromQL, SLIs e Recording Rules", table_cell_style)],
            [Paragraph("Grafana", table_header_style), Paragraph("http://localhost:3000", table_url_style), Paragraph("<b>admin</b> / <b>admin</b> (Dashboards SRE)", table_cell_style)],
            [Paragraph("Alertmanager", table_header_style), Paragraph("http://localhost:9093", table_url_style), Paragraph("Alertas ativos, rotas e inibições", table_cell_style)],
        ],
        colWidths=[150, 195, 187],
    )
    t_k8s.setStyle(
        TableStyle(
            [
                ("ROWBACKGROUNDS", (0, 0), (-1, -1), [colors.HexColor("#ffffff"), colors.HexColor("#f8fafc")]),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#d0d7de")),
                ("TOPPADDING", (0, 0), (-1, -1), 3),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
                ("LEFTPADDING", (0, 0), (-1, -1), 6),
                ("RIGHTPADDING", (0, 0), (-1, -1), 6),
            ]
        )
    )
    story.append(t_k8s)
    story.append(Spacer(1, 4))

    story.append(Paragraph("Passo 5: Desligar e limpar todos os recursos do cluster:", step_title_style))
    story.append(Spacer(1, 2))
    story.append(create_code_block(["make clean"]))

    # =========================================================================
    # PÁGINA 3 — Validação, Testes Automatizados & Critérios de Aceite v3.5
    # =========================================================================
    story.append(PageBreak())
    story.append(Spacer(1, 4))

    story.append(create_section_header("Validação Rápida da Suíte de Testes & Qualidade (v3.5)", "QUALIDADE & ACEITE", "#1a7f37"))
    story.append(Spacer(1, 4))
    story.append(
        Paragraph(
            "Rotina completa de validação contínua para certificar que todos os 16 cenários de produção, o motor RAG semântico, "
            "os runbooks estruturados em 5 fases e as novas proteções técnicas da v3.5 estão 100% íntegros e operacionais.",
            sec_desc_style,
        )
    )
    story.append(Spacer(1, 6))

    # Passo 1: Script de Validação Automatizada da v3.5
    story.append(Paragraph("Passo 1: Script de Validação Automatizada da v3.5 (12 Critérios de Aceite):", step_title_style))
    story.append(Spacer(1, 2))
    story.append(
        create_code_block(
            [
                "bash scripts/verify_v3.5.sh",
                "# Executa a verificação dos 12 critérios de aceite: sintaxe, Pydantic V2 ConfigDict,",
                "# TTL cache, async embeddings, gzip, security headers, rate limit e testes unitários.",
            ]
        )
    )
    story.append(Spacer(1, 5))

    # Passo 2: Testes unitários com pytest
    story.append(Paragraph("Passo 2: Executar a suíte de testes unitários e de integração:", step_title_style))
    story.append(Spacer(1, 2))
    story.append(
        create_code_block(
            [
                "make test",
                "# Executa: PYTHONPATH=.:app ./app/.venv/bin/pytest tests/ -v",
            ]
        )
    )
    story.append(Spacer(1, 5))

    # Tabela de módulos testados
    story.append(Paragraph("Módulos e Escopo de Testes Automatizados Cobertos:", step_title_style))
    story.append(Spacer(1, 3))

    t_tests_scope = Table(
        [
            [
                Paragraph("<b>Módulo de Teste</b>", table_header_style),
                Paragraph("<b>Arquivo</b>", table_header_style),
                Paragraph("<b>O que é validado</b>", table_header_style),
            ],
            [
                Paragraph("Cenários de Incidente", table_cell_style),
                Paragraph("<code>tests/test_incidents.py</code>", table_cell_style),
                Paragraph("16 cenários de produção, integridade dos runbooks em 5 fases, balanceamento em 4 dificuldades (Fácil, Médio, Difícil, Extremo) e histórico de zero-repetição.", table_cell_style),
            ],
            [
                Paragraph("Chaos Monkey 2.0", table_cell_style),
                Paragraph("<code>tests/test_chaos.py</code>", table_cell_style),
                Paragraph("Injeção controlada de falhas HTTP 500, auditoria em tempo real, geração de eventos de incidentes e exportação de métricas RED.", table_cell_style),
            ],
            [
                Paragraph("Motor RAG Semântico", table_cell_style),
                Paragraph("<code>tests/test_rag.py</code>", table_cell_style),
                Paragraph("Indexação vetorial de runbooks, inferência com SentenceTransformer (asyncio.to_thread), cálculo de similaridade e acurácia de recuperação.", table_cell_style),
            ],
        ],
        colWidths=[130, 142, 260],
    )
    t_tests_scope.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#f0f4f9")),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.HexColor("#ffffff"), colors.HexColor("#f8fafc")]),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#d0d7de")),
                ("TOPPADDING", (0, 0), (-1, -1), 3.5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 3.5),
                ("LEFTPADDING", (0, 0), (-1, -1), 6),
                ("RIGHTPADDING", (0, 0), (-1, -1), 6),
            ]
        )
    )
    story.append(t_tests_scope)
    story.append(Spacer(1, 6))

    # Passo 3: Avaliação de IA (SRE-Eval)
    story.append(Paragraph("Passo 3: Executar a avaliação de acurácia com o benchmark SRE-Eval:", step_title_style))
    story.append(Spacer(1, 2))
    story.append(
        create_code_block(
            [
                "make eval",
                "# Executa: PYTHONPATH=.:app ./app/.venv/bin/python tests/eval/evaluator.py",
                "# Gera o relatório de acurácia, relevância semântica e latência de resposta da IA.",
            ]
        )
    )
    story.append(Spacer(1, 6))

    # Box de Dicas de Troubleshooting e Observabilidade
    tb_title = '<font face="Helvetica-Bold" size="8.5" color="#0969da"><b>💡 Dicas de Observabilidade &amp; Troubleshooting Rápido no Lab:</b></font>'
    tb_body = (
        "• <b>Status dos SLOs em Tempo Real:</b> Execute <code>make slo-status</code> para verificar a taxa de queima (Burn Rate) de Error Budget instantânea.<br/>"
        "• <b>Simulação de Carga Contínua:</b> Execute <code>make load-test</code> para disparar requisições concorrentes e testar o HPA e o Rate Limiter.<br/>"
        "• <b>Auditoria do Chaos Monkey:</b> Monitore o terminal ou os logs com <code>docker compose logs -f api</code> para inspecionar falhas injetadas.<br/>"
        "• <b>Verificação de Health Cache:</b> Execute requisições sucessivas a <code>/healthz</code> para constatar a resposta sub-milissegundo via cache TTL."
    )
    tb_p = Paragraph(f"{tb_title}<br/>{tb_body}", ParagraphStyle("TBBox", fontName="Helvetica", fontSize=7.8, leading=10.8, textColor=colors.HexColor("#1f2328")))
    tb_table = Table([[tb_p]], colWidths=[532])
    tb_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#f6f8fa")),
                ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#d0d7de")),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                ("LEFTPADDING", (0, 0), (-1, -1), 7),
                ("RIGHTPADDING", (0, 0), (-1, -1), 7),
            ]
        )
    )
    story.append(tb_table)

    # Build do Documento com o NumberedCanvas
    doc.build(story, canvasmaker=NumberedCanvas)
    print(f"PDF gerado com sucesso: {filename}")


if __name__ == "__main__":
    build_pdf()
