"""
ESPE — Sistema de Gestão de Aulas
App principal (Streamlit). Dois acessos: Gestora e Professora.
"""
import streamlit as st
import pandas as pd
from datetime import date

import branding as B
import db
import pdf_gen as pdf

st.set_page_config(page_title="ESPE — Gestão", page_icon="🎒", layout="wide")
st.markdown(B.CSS, unsafe_allow_html=True)

# Mês de trabalho padrão do app
MES_LABEL = "Abril"
MES_ANO = "Abril 2026"


# ---------------- LOGIN ----------------
def tela_login():
    _, mid, _ = st.columns([1, 1.2, 1])
    with mid:
        st.markdown(B.LOGO_HTML, unsafe_allow_html=True)
        st.write("")
        st.subheader("Sistema de gestão de aulas")
        papel = st.radio("Entrar como:", ["Gestora", "Professora"], horizontal=True)

        if papel == "Gestora":
            senha = st.text_input("Senha de acesso", type="password")
            if st.button("Entrar", type="primary", use_container_width=True):
                if senha == st.secrets.get("SENHA_GESTORA", "espe2026"):
                    st.session_state.papel = "gestora"
                    st.rerun()
                else:
                    st.error("Senha incorreta.")
        else:
            profs = db.listar_professoras()
            nome = st.selectbox("Quem é você?", [p["nome"] for p in profs])
            pin = st.text_input("Seu PIN", type="password", max_chars=4)
            if st.button("Entrar", type="primary", use_container_width=True):
                p = next((x for x in profs if x["nome"] == nome), None)
                if p and pin == p["pin"]:
                    st.session_state.papel = "prof"
                    st.session_state.prof = p
                    st.rerun()
                else:
                    st.error("PIN incorreto.")


# ---------------- HELPERS UI ----------------
def kpi(col, lbl, val, dlt="", cor=B.AZUL):
    col.markdown(
        f'<div class="kpi" style="border-left-color:{cor}">'
        f'<div class="lbl">{lbl}</div><div class="val">{val}</div>'
        f'<div class="dlt">{dlt}</div></div>', unsafe_allow_html=True)


def brl(n):
    return "R$ " + f"{float(n):,.0f}".replace(",", ".")


def calc_fechamento(aulas):
    horas = sum(a["duracao"] for a in aulas)
    repasse = sum(a["rep_hora"] * a["duracao"] for a in aulas)
    ajuda = sum(a["rep_ajuda"] for a in aulas)
    return {"total_aulas": len(aulas), "total_horas": horas,
            "total_repasse": repasse, "total_ajuda": ajuda,
            "total": repasse + ajuda}


# ================= GESTORA =================
def app_gestora():
    with st.sidebar:
        st.markdown(B.LOGO_HTML, unsafe_allow_html=True)
        st.write("")
        page = st.radio("Menu", ["📊 Painel", "📅 Aulas", "💰 Recebimentos",
                                  "👦 Alunos", "🎒 Professoras", "📑 Fechamentos"],
                        label_visibility="collapsed")
        st.divider()
        if st.button("↩ Sair"):
            st.session_state.clear(); st.rerun()

    if "Painel" in page:       g_painel()
    elif "Aulas" in page:      g_aulas()
    elif "Recebimentos" in page: g_recebimentos()
    elif "Alunos" in page:     g_alunos()
    elif "Professoras" in page: g_profs()
    elif "Fechamentos" in page: g_fechamentos()


def g_painel():
    st.title("Painel financeiro")
    st.caption("Visão geral de 2026 — atualizado em tempo real")
    aulas = db.listar_aulas()
    alunos = db.listar_alunos()

    receita = sum(a["valor_aula"] for a in aulas)
    repasse = sum(a["total_repasse"] for a in aulas)
    margem = receita - repasse
    horas = sum(a["duracao"] for a in aulas)
    n = len(aulas)
    c = st.columns(6)
    kpi(c[0], "Receita total", brl(receita), f"{n} aulas", B.VERDE)
    kpi(c[1], "Repasse prof.", brl(repasse), "", B.AZUL)
    kpi(c[2], "Margem bruta", brl(margem),
        f"{margem/receita*100:.1f}% margem" if receita else "", B.AMARELO)
    kpi(c[3], "Ticket médio", brl(receita/n) if n else "R$ 0", "por aula", B.CORAL)
    kpi(c[4], "Total de horas", f"{horas:.0f} h", "", B.LILAS)
    kpi(c[5], "Receita / hora", brl(receita/horas) if horas else "R$ 0", "", B.OK)

    st.write("")
    # Alertas
    negs = [a for a in alunos
            if (a["horas_contratadas"] - a["horas_usadas"]) < 0]
    pend = [a for a in aulas if a["status_pagamento"] == "Pendente"]
    if negs or pend:
        st.subheader("Alertas")
        if negs:
            nomes = ", ".join(f"{a['nome'].split()[0]} ({a['horas_contratadas']-a['horas_usadas']:.0f}h)"
                              for a in negs)
            st.markdown(f'<div class="alert warn">⚠️ <b>{len(negs)} aluno(s) com saldo '
                        f'de horas negativo</b> — {nomes}. Hora de renovar pacote.</div>',
                        unsafe_allow_html=True)
        if pend:
            tot = sum(a["valor_aula"] for a in pend)
            st.markdown(f'<div class="alert info">💸 <b>{len(pend)} aulas com pagamento '
                        f'pendente</b> somando {brl(tot)}.</div>', unsafe_allow_html=True)

    st.write("")
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Desempenho por mês")
        df = pd.DataFrame(aulas)
        if not df.empty:
            g = (df.groupby("mes")[["valor_aula", "total_repasse"]].sum()
                   .rename(columns={"valor_aula": "Receita",
                                    "total_repasse": "Repasse"}))
            ordem = ["Fevereiro", "Março", "Abril", "Maio", "Junho",
                     "Julho", "Agosto", "Setembro", "Outubro", "Novembro",
                     "Dezembro"]
            g = g.reindex([m for m in ordem if m in g.index])
            st.bar_chart(g, color=[B.AZUL, B.AMARELO])
    with col2:
        st.subheader("Repasse por professora")
        df = pd.DataFrame(aulas)
        if not df.empty:
            df["prof"] = df["professoras"].apply(lambda x: x["nome"])
            g = df.groupby("prof")["total_repasse"].sum().sort_values(ascending=False)
            st.bar_chart(g, color=B.LILAS, horizontal=True)

    st.subheader("Receita por aluno")
    df = pd.DataFrame(aulas)
    if not df.empty:
        df["al"] = df["alunos"].apply(lambda x: x["nome"])
        g = df.groupby("al")["valor_aula"].sum().sort_values(ascending=False)
        st.bar_chart(g, color=B.VERDE, horizontal=True)


def g_aulas():
    st.title("Aulas")
    st.caption("Todas as aulas registradas")
    profs = db.listar_professoras()
    alunos = db.listar_alunos()

    with st.expander("➕ Registrar nova aula"):
        c = st.columns(4)
        a_aluno = c[0].selectbox("Aluno", [a["nome"] for a in alunos], key="na_aluno")
        a_prof = c[1].selectbox("Professora", [p["nome"] for p in profs], key="na_prof")
        a_data = c[2].date_input("Data", value=date.today(), key="na_data")
        a_dur = c[3].number_input("Duração (h)", 0.5, 5.0, 1.0, 0.5, key="na_dur")
        c2 = st.columns(4)
        al = next(x for x in alunos if x["nome"] == a_aluno)
        pr = next(x for x in profs if x["nome"] == a_prof)
        valor_sug = al["valor_hora"] * a_dur
        a_valor = c2[0].number_input("Valor da aula (R$)", 0.0, value=float(valor_sug),
                                     key="na_valor")
        a_hora = c2[1].text_input("Horário", "14:00", key="na_hora")
        if c2[3].button("Salvar aula", type="primary"):
            mes_nome = ["", "Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho",
                        "Julho", "Agosto", "Setembro", "Outubro", "Novembro",
                        "Dezembro"][a_data.month]
            db.inserir_aula({
                "data": str(a_data), "mes": mes_nome,
                "semana": a_data.isocalendar()[1],
                "aluno_id": al["id"], "professora_id": pr["id"],
                "horario": a_hora, "duracao": a_dur,
                "rep_hora": pr["repasse_hora"], "rep_ajuda": pr["ajuda_custo"],
                "total_repasse": pr["repasse_hora"] * a_dur + pr["ajuda_custo"],
                "valor_aula": a_valor, "status_pagamento": "Pendente"})
            st.success("Aula registrada!"); st.rerun()

    aulas = db.listar_aulas()
    rows = [{"id": a["id"], "Data": pdf._data_br(a["data"]),
             "Aluno": a["alunos"]["nome"], "Professora": a["professoras"]["nome"],
             "Duração": f"{a['duracao']:.0f}h", "Valor": brl(a["valor_aula"]),
             "Repasse": brl(a["total_repasse"]), "Pagamento": a["status_pagamento"]}
            for a in aulas]
    st.dataframe(pd.DataFrame(rows).drop(columns=["id"]), use_container_width=True,
                 hide_index=True)

    st.divider()
    st.subheader("Gerar recibo de aula")
    opts = {f"{pdf._data_br(a['data'])} — {a['alunos']['nome']} ({brl(a['valor_aula'])})": a
            for a in aulas}
    sel = st.selectbox("Escolha a aula", list(opts.keys()))
    if sel:
        a = opts[sel]
        st.download_button("📄 Baixar recibo (PDF)", pdf.recibo_aula(a),
                           file_name=f"recibo_{a['alunos']['nome'].split()[0]}.pdf",
                           mime="application/pdf")


def g_recebimentos():
    st.title("Recebimentos")
    st.caption("Controle do que cada família já pagou")
    aulas = db.listar_aulas(mes=MES_LABEL)
    rec = sum(a["valor_aula"] for a in aulas if a["status_pagamento"] == "Pago")
    pen = sum(a["valor_aula"] for a in aulas if a["status_pagamento"] == "Pendente")
    c = st.columns(3)
    kpi(c[0], "Recebido", brl(rec), "", B.OK)
    kpi(c[1], "A receber", brl(pen), "", B.CORAL)
    taxa = rec / (rec + pen) * 100 if (rec + pen) else 0
    kpi(c[2], "Taxa de pagamento", f"{taxa:.0f}%", "do faturado", B.AMARELO)

    st.write("")
    st.subheader(f"Aulas — {MES_ANO}")
    for a in aulas:
        cols = st.columns([1.2, 2.5, 1.2, 1.3, 1.5, 1.6])
        cols[0].write(pdf._data_br(a["data"]))
        cols[1].write(f"**{a['alunos']['nome']}**")
        cols[2].write(brl(a["valor_aula"]))
        cols[3].write(a["status_pagamento"])
        cols[4].write(pdf._data_br(a["recebido_em"]) if a["recebido_em"] else "—")
        if a["status_pagamento"] == "Pago":
            if cols[5].button("Desfazer", key=f"d{a['id']}"):
                db.marcar_pendente(a["id"]); st.rerun()
        else:
            if cols[5].button("Marcar recebido", key=f"p{a['id']}", type="primary"):
                db.marcar_pago(a["id"], date.today()); st.rerun()


def g_alunos():
    st.title("Alunos")
    st.caption("Cadastro, pacotes e saldo de horas")
    pacotes = db.listar_pacotes()
    with st.expander("➕ Novo aluno"):
        c = st.columns(4)
        nome = c[0].text_input("Nome")
        serie = c[1].text_input("Série")
        pac = c[2].selectbox("Pacote", [p["codigo"] for p in pacotes])
        p = next(x for x in pacotes if x["codigo"] == pac)
        if c[3].button("Salvar aluno", type="primary") and nome:
            db.inserir_aluno({"nome": nome, "serie": serie, "status": "Ativo",
                              "pacote_ativo": pac, "valor_hora": p["valor_hora"],
                              "horas_usadas": 0, "horas_contratadas": p["horas"]})
            st.success("Aluno cadastrado!"); st.rerun()

    alunos = db.listar_alunos()
    aulas = db.listar_aulas()
    for al in alunos:
        saldo = al["horas_contratadas"] - al["horas_usadas"]
        cor = B.CORAL if saldo < 0 else B.OK
        cols = st.columns([2.2, 1.3, 1.1, 1.3, 1.4, 1.5])
        cols[0].write(f"**{al['nome']}**")
        cols[1].write(al.get("serie") or "—")
        cols[2].write(al["pacote_ativo"])
        cols[3].write(f"{al['horas_usadas']:.0f}/{al['horas_contratadas']:.0f}h")
        cols[4].markdown(f"<span style='color:{cor};font-weight:700'>"
                         f"{saldo:+.0f}h</span>", unsafe_allow_html=True)
        aulas_al = [a for a in aulas if a["alunos"]["nome"] == al["nome"]
                    and a["mes"] == MES_LABEL]
        cols[5].download_button("📄 Extrato", pdf.extrato_aluno(al, aulas_al, MES_ANO),
                                file_name=f"extrato_{al['nome'].split()[0]}.pdf",
                                mime="application/pdf", key=f"ext{al['id']}")


def g_profs():
    st.title("Professoras")
    st.caption("Equipe e valores de repasse")
    profs = db.listar_professoras()
    aulas = db.listar_aulas(mes=MES_LABEL)
    with st.expander("➕ Nova professora"):
        c = st.columns(4)
        nome = c[0].text_input("Nome", key="np_nome")
        pin = c[1].text_input("PIN (4 dígitos)", "1234", max_chars=4, key="np_pin")
        if c[3].button("Salvar professora", type="primary") and nome:
            db.inserir_professora({"nome": nome, "repasse_hora": 60, "ajuda_custo": 15,
                                   "status": "Ativa", "pin": pin})
            st.success("Professora cadastrada!"); st.rerun()

    for p in profs:
        aulas_p = [a for a in aulas if a["professoras"]["nome"] == p["nome"]]
        f = calc_fechamento(aulas_p)
        cols = st.columns([1.8, 1.4, 1.4, 1.2, 1.6])
        cols[0].write(f"**{p['nome']}**")
        cols[1].write(f"{brl(p['repasse_hora'])}/h")
        cols[2].write(f"{brl(p['ajuda_custo'])}/aula")
        cols[3].write(f"{f['total_aulas']} aulas")
        cols[4].write(f"A receber: **{brl(f['total'])}**")


def g_fechamentos():
    st.title("Fechamentos de repasse")
    st.caption(f"Feche o mês e libere o valor para a professora ver — {MES_ANO}")
    profs = db.listar_professoras()
    aulas = db.listar_aulas(mes=MES_LABEL)

    for p in profs:
        aulas_p = [a for a in aulas if a["professoras"]["nome"] == p["nome"]]
        if not aulas_p:
            continue
        f = calc_fechamento(aulas_p)
        fech = db.get_fechamento(p["id"], MES_ANO)
        fechado = fech["fechado"] if fech else False

        cols = st.columns([1.6, 1, 1, 1.3, 1.2, 1.3, 1.3])
        cols[0].write(f"**{p['nome']}**")
        cols[1].write(f"{f['total_aulas']} aulas")
        cols[2].write(f"{f['total_horas']:.0f}h")
        cols[3].write(f"Repasse {brl(f['total_repasse'])}")
        cols[4].write(f"**{brl(f['total'])}**")
        cols[5].write("🟢 Fechado" if fechado else "🟡 Aberto")
        label = "Reabrir" if fechado else "Fechar mês"
        if cols[6].button(label, key=f"f{p['id']}", type="primary" if not fechado else "secondary"):
            db.upsert_fechamento({
                "professora_id": p["id"], "mes": MES_ANO, "fechado": not fechado,
                "fechado_em": str(date.today()) if not fechado else None,
                "total_aulas": f["total_aulas"], "total_horas": f["total_horas"],
                "total_repasse": f["total_repasse"], "total_ajuda": f["total_ajuda"],
                "total": f["total"]})
            st.rerun()

        fdata = {**f, "fechado": fechado}
        cols_pdf = st.columns([6, 1.3])
        cols_pdf[1].download_button(
            "📑 PDF", pdf.fechamento_professora(p["nome"], aulas_p, fdata, MES_ANO),
            file_name=f"fechamento_{p['nome']}.pdf", mime="application/pdf",
            key=f"pdf{p['id']}")


# ================= PROFESSORA =================
def app_professora():
    p = st.session_state.prof
    with st.sidebar:
        st.markdown(B.LOGO_HTML, unsafe_allow_html=True)
        st.write("")
        st.write(f"Olá, **{p['nome']}** 🎒")
        page = st.radio("Menu", ["📅 Minhas aulas", "💰 Meu repasse"],
                        label_visibility="collapsed")
        st.divider()
        if st.button("↩ Sair"):
            st.session_state.clear(); st.rerun()

    aulas = db.listar_aulas(professora_id=p["id"], mes=MES_LABEL)

    if "Minhas aulas" in page:
        st.title("Minhas aulas")
        st.caption(f"Olá, {p['nome']}! Suas aulas em {MES_ANO}")
        f = calc_fechamento(aulas)
        fech = db.get_fechamento(p["id"], MES_ANO)
        c = st.columns(3)
        kpi(c[0], "Aulas no mês", f["total_aulas"], "", B.VERDE)
        kpi(c[1], "Horas dadas", f"{f['total_horas']:.0f} h", "", B.AZUL)
        kpi(c[2], "Status do mês",
            "Fechado ✓" if (fech and fech["fechado"]) else "Em aberto", "", B.AMARELO)
        st.write("")
        rows = [{"Data": pdf._data_br(a["data"]), "Aluno": a["alunos"]["nome"],
                 "Duração": f"{a['duracao']:.0f}h"} for a in aulas]
        st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

    else:  # Meu repasse
        st.title("Meu repasse")
        st.caption("O quanto você tem a receber")
        fech = db.get_fechamento(p["id"], MES_ANO)
        if fech and fech["fechado"]:
            st.markdown(
                f'<div class="fechado"><h3 style="margin:0;opacity:.9">'
                f'Seu repasse de {MES_LABEL} está fechado 🎉</h3>'
                f'<div class="v">{brl(fech["total"])}</div>'
                f'<div style="opacity:.92;line-height:1.8">'
                f'• {fech["total_horas"]:.0f}h × {brl(60)} = <b>{brl(fech["total_repasse"])}</b><br>'
                f'• Ajuda de custo: {fech["total_aulas"]} aulas × {brl(15)} = '
                f'<b>{brl(fech["total_ajuda"])}</b><br>'
                f'• <b>Total a receber: {brl(fech["total"])}</b></div></div>',
                unsafe_allow_html=True)
            st.write("")
            st.subheader("Como esse valor foi calculado")
            st.dataframe(pd.DataFrame([
                {"Item": "Horas de aula", "Cálculo": f"{fech['total_horas']:.0f}h × {brl(60)}",
                 "Valor": brl(fech["total_repasse"])},
                {"Item": "Ajuda de custo", "Cálculo": f"{fech['total_aulas']} × {brl(15)}",
                 "Valor": brl(fech["total_ajuda"])},
                {"Item": "Total", "Cálculo": "", "Valor": brl(fech["total"])},
            ]), use_container_width=True, hide_index=True)
        else:
            st.markdown(
                f'<div class="aguardando">⏳<br><br>'
                f'<b>O repasse de {MES_LABEL} ainda não foi fechado pela ESPE.</b><br>'
                f'Assim que a gestora fechar o mês, o valor e o detalhamento aparecem aqui.'
                f'</div>', unsafe_allow_html=True)


# ---------------- ROTEAMENTO ----------------
if "papel" not in st.session_state:
    tela_login()
elif st.session_state.papel == "gestora":
    app_gestora()
else:
    app_professora()
