"""Conexão com o Supabase e funções de consulta/escrita."""
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


def listar_aulas(professora_id=None, mes=None):
    q = get_client().table("aulas").select(
        "*, alunos(nome,serie,pacote_ativo,valor_hora), professoras(nome)"
    )
    if professora_id:
        q = q.eq("professora_id", professora_id)
    if mes:
        q = q.eq("mes", mes)
    return q.order("data").execute().data


def get_fechamento(professora_id, mes):
    r = (get_client().table("fechamentos").select("*")
         .eq("professora_id", professora_id).eq("mes", mes).execute().data)
    return r[0] if r else None


def listar_fechamentos(mes):
    return (get_client().table("fechamentos").select("*, professoras(nome)")
            .eq("mes", mes).execute().data)


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
