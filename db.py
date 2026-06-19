"""Conexão com o Supabase e funções de consulta/escrita.

As consultas de aulas montam os 'joins' (aluno e professora) em Python,
em vez de usar a sintaxe embutida do PostgREST. Isso evita problemas de
compatibilidade entre versões da biblioteca supabase-py.
"""
import streamlit as st
from supabase import create_client


@st.cache_resource
def get_client():
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    return create_client(url, key)


# ---------- LEITURAS ----------
def listar_professoras():
    return get_client().table("professoras").select("*").order("nome").execute().data


def listar_alunos():
    return get_client().table("alunos").select("*").order("nome").execute().data


def listar_pacotes():
    return get_client().table("pacotes").select("*").execute().data


def _mapa(tabela, campos):
    """Devolve {id: {campos...}} para montar joins em memória."""
    linhas = get_client().table(tabela).select("*").execute().data
    out = {}
    for r in linhas:
        out[r["id"]] = {c: r.get(c) for c in campos}
    return out


def listar_aulas(professora_id=None, mes=None):
    q = get_client().table("aulas").select("*")
    if professora_id:
        q = q.eq("professora_id", professora_id)
    if mes:
        q = q.eq("mes", mes)
    aulas = q.order("data").execute().data

    alunos = _mapa("alunos", ["nome", "serie", "pacote_ativo", "valor_hora"])
    profs = _mapa("professoras", ["nome"])

    for a in aulas:
        a["alunos"] = alunos.get(a.get("aluno_id"), {"nome": "—"})
        a["professoras"] = profs.get(a.get("professora_id"), {"nome": "—"})
    return aulas


def get_fechamento(professora_id, mes):
    r = (get_client().table("fechamentos").select("*")
         .eq("professora_id", professora_id).eq("mes", mes).execute().data)
    return r[0] if r else None


def listar_fechamentos(mes):
    fechs = (get_client().table("fechamentos").select("*")
             .eq("mes", mes).execute().data)
    profs = _mapa("professoras", ["nome"])
    for f in fechs:
        f["professoras"] = profs.get(f.get("professora_id"), {"nome": "—"})
    return fechs


# ---------- ESCRITAS ----------
def marcar_pago(aula_id, data_recebido):
    get_client().table("aulas").update(
        {"status_pagamento": "Pago", "recebido_em": str(data_recebido)}
    ).eq("id", aula_id).execute()


def marcar_pendente(aula_id):
    get_client().table("aulas").update(
        {"status_pagamento": "Pendente", "recebido_em": None}
    ).eq("id", aula_id).execute()


def inserir_aula(dados):
    get_client().table("aulas").insert(dados).execute()


def inserir_aluno(dados):
    get_client().table("alunos").insert(dados).execute()


def inserir_professora(dados):
    get_client().table("professoras").insert(dados).execute()


def upsert_fechamento(dados):
    """Cria ou atualiza o fechamento de uma professora num mês."""
    get_client().table("fechamentos").upsert(
        dados, on_conflict="professora_id,mes"
    ).execute()


def atualizar_pin(professora_id, novo_pin):
    get_client().table("professoras").update({"pin": novo_pin}).eq(
        "id", professora_id).execute()
