"""Geração dos PDFs da ESPE: recibo de aula, extrato do aluno, fechamento da professora.
Usa reportlab — gera o arquivo em memória e devolve os bytes para download no Streamlit.
"""
from io import BytesIO
from datetime import date
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer, Table,
                                TableStyle)
from reportlab.lib.enums import TA_RIGHT, TA_CENTER

VERDE = colors.HexColor("#acc900")
AZUL = colors.HexColor("#516ed6")
AMARELO = colors.HexColor("#f9bf41")
CORAL = colors.HexColor("#e96e4c")
CREME = colors.HexColor("#f9eedc")
TINTA = colors.HexColor("#2a2a3c")
CINZA = colors.HexColor("#6b6b7d")


def brl(n):
    return "R$ " + f"{n:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def _styles():
    s = getSampleStyleSheet()
    s.add(ParagraphStyle("Sub", parent=s["Normal"], fontSize=8, textColor=CINZA))
    s.add(ParagraphStyle("H", parent=s["Heading1"], fontSize=15, textColor=AZUL,
                         spaceAfter=10))
    s.add(ParagraphStyle("Meta", parent=s["Normal"], fontSize=8, textColor=CINZA,
                         alignment=TA_RIGHT))
    s.add(ParagraphStyle("Foot", parent=s["Normal"], fontSize=8, textColor=CINZA,
                         alignment=TA_CENTER))
    s.add(ParagraphStyle("Note", parent=s["Normal"], fontSize=8.5, textColor=CINZA,
                         leading=13))
    return s


def _logo_table(st):
    """Cabeçalho com a 'logo' ESPE colorida em texto e meta à direita."""
    logo = Paragraph(
        '<font color="#e96e4c"><b>E</b></font>'
        '<font color="#f9bf41"><b>S</b></font>'
        '<font color="#516ed6"><b>P</b></font>'
        '<font color="#acc900"><b>E</b></font>',
        ParagraphStyle("L", fontSize=26, leading=28))
    sub = Paragraph("educação sensorial personalizada", st["Sub"])
    meta = Paragraph(f"Rio de Janeiro<br/>Emitido em {date.today().strftime('%d/%m/%Y')}",
                     st["Meta"])
    t = Table([[[logo, sub], meta]], colWidths=[100 * mm, 70 * mm])
    t.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LINEBELOW", (0, 0), (-1, -1), 2, AZUL),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
    ]))
    return t


def _tbl(data, col_widths, header=True):
    t = Table(data, colWidths=col_widths)
    style = [
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, CREME]),
        ("LINEBELOW", (0, 0), (-1, 0), 1, AZUL),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
    ]
    if header:
        style += [("TEXTCOLOR", (0, 0), (-1, 0), CINZA),
                  ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold")]
    t.setStyle(TableStyle(style))
    return t


def _total_box(label, valor):
    t = Table([[label, brl(valor)]], colWidths=[120 * mm, 50 * mm])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), CREME),
        ("TEXTCOLOR", (1, 0), (1, 0), AZUL),
        ("FONTNAME", (1, 0), (1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (1, 0), (1, 0), 16),
        ("FONTSIZE", (0, 0), (0, 0), 11),
        ("ALIGN", (1, 0), (1, 0), "RIGHT"),
        ("TOPPADDING", (0, 0), (-1, -1), 12),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 12),
        ("LEFTPADDING", (0, 0), (-1, -1), 14),
        ("RIGHTPADDING", (0, 0), (-1, -1), 14),
        ("ROUNDEDCORNERS", [8, 8, 8, 8]),
    ]))
    return t


def _build(elements):
    buf = BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4, topMargin=18 * mm,
                            bottomMargin=18 * mm, leftMargin=20 * mm,
                            rightMargin=20 * mm)
    doc.build(elements)
    buf.seek(0)
    return buf.getvalue()


# ============ 1) RECIBO DE AULA ============
def recibo_aula(aula):
    st = _styles()
    aluno = aula["alunos"]["nome"]
    prof = aula["professoras"]["nome"]
    e = [
        _logo_table(st), Spacer(1, 14),
        Paragraph("Recibo de aula particular", st["H"]),
        _tbl([["Aluno", aluno, "Professora", prof],
              ["Data", _data_br(aula["data"]), "Duração", f"{_num(aula['duracao'])} h"]],
             [25 * mm, 60 * mm, 28 * mm, 57 * mm], header=False),
        Spacer(1, 12),
        _tbl([["Descrição", "Qtd", "Valor"],
              ["Aula particular personalizada", f"{_num(aula['duracao'])}h",
               brl(aula["valor_aula"])]],
             [110 * mm, 30 * mm, 30 * mm]),
        Spacer(1, 10),
        _total_box("Total da aula", aula["valor_aula"]),
        Spacer(1, 14),
        Paragraph(
            f"Recebemos a importância acima referente à aula particular prestada pela "
            f"ESPE — Educação Sensorial Personalizada. "
            f"Situação do pagamento: <b>{aula['status_pagamento']}</b>"
            + (f", recebido em {_data_br(aula['recebido_em'])}." if aula.get('recebido_em') else "."),
            st["Note"]),
        Spacer(1, 22),
        Paragraph("ESPE • educação que acolhe, conecta e transforma", st["Foot"]),
    ]
    return _build(e)


# ============ 2) EXTRATO DO ALUNO ============
def extrato_aluno(aluno, aulas, mes_label):
    st = _styles()
    total = sum(a["valor_aula"] for a in aulas)
    pago = sum(a["valor_aula"] for a in aulas if a["status_pagamento"] == "Pago")
    saldo = aluno["horas_contratadas"] - aluno["horas_usadas"]
    linhas = [["Data", "Professora", "Duração", "Valor", "Pgto"]]
    for a in aulas:
        linhas.append([_data_br(a["data"]), a["professoras"]["nome"],
                       f"{_num(a['duracao'])}h", brl(a["valor_aula"]),
                       a["status_pagamento"]])
    if not aulas:
        linhas.append(["—", "Sem aulas no período", "", "", ""])
    e = [
        _logo_table(st), Spacer(1, 14),
        Paragraph(f"Extrato de aulas — {mes_label}", st["H"]),
        _tbl([["Aluno", aluno["nome"], "Série", aluno.get("serie") or "—"],
              ["Pacote", f"{aluno.get('pacote_ativo')} ({brl(aluno['valor_hora'])}/h)",
               "Saldo de horas", f"{_num(saldo)}h"]],
             [25 * mm, 65 * mm, 30 * mm, 50 * mm], header=False),
        Spacer(1, 12),
        _tbl(linhas, [28 * mm, 45 * mm, 25 * mm, 35 * mm, 27 * mm]),
        Spacer(1, 10),
        _total_box(f"Total do mês  ({brl(pago)} já pago)", total),
        Spacer(1, 14),
        Paragraph(
            f"Extrato detalhado das aulas particulares do mês, referente ao pacote "
            f"<b>{aluno.get('pacote_ativo')}</b>. Em caso de dúvida sobre o pacote ou "
            f"saldo de horas, fale com a coordenação da ESPE.", st["Note"]),
        Spacer(1, 22),
        Paragraph("ESPE • educação que acolhe, conecta e transforma", st["Foot"]),
    ]
    return _build(e)


# ============ 3) FECHAMENTO DA PROFESSORA ============
def fechamento_professora(prof_nome, aulas, fechamento, mes_label):
    st = _styles()
    linhas = [["Data", "Aluno", "Duração", "Repasse"]]
    for a in aulas:
        linhas.append([_data_br(a["data"]), a["alunos"]["nome"],
                       f"{_num(a['duracao'])}h", brl(a["total_repasse"])])
    e = [
        _logo_table(st), Spacer(1, 14),
        Paragraph(f"Fechamento de repasse — {mes_label}", st["H"]),
        _tbl([["Professora", prof_nome, "Aulas no mês", str(fechamento["total_aulas"])],
              ["Horas", f"{_num(fechamento['total_horas'])}h", "Situação",
               "Fechado" if fechamento["fechado"] else "Em aberto"]],
             [28 * mm, 55 * mm, 32 * mm, 55 * mm], header=False),
        Spacer(1, 12),
        _tbl(linhas, [30 * mm, 70 * mm, 30 * mm, 40 * mm]),
        Spacer(1, 10),
        _tbl([["Repasse por hora",
               f"{_num(fechamento['total_horas'])}h × {brl(60)}",
               brl(fechamento["total_repasse"])],
              ["Ajuda de custo",
               f"{fechamento['total_aulas']} × {brl(15)}",
               brl(fechamento["total_ajuda"])]],
             [70 * mm, 60 * mm, 40 * mm], header=False),
        Spacer(1, 8),
        _total_box("Total a pagar", fechamento["total"]),
        Spacer(1, 14),
        Paragraph("Documento de fechamento de repasse referente às aulas prestadas no mês.",
                  st["Note"]),
        Spacer(1, 22),
        Paragraph("ESPE • educação que acolhe, conecta e transforma", st["Foot"]),
    ]
    return _build(e)


# ---------- helpers ----------
def _num(n):
    n = float(n)
    return int(n) if n == int(n) else n


def _data_br(d):
    if not d:
        return "—"
    s = str(d)
    if "-" in s and len(s) >= 10:
        a, m, dia = s[:10].split("-")
        return f"{dia}/{m}/{a}"
    return s
