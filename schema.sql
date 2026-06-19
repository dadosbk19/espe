-- ============================================================
--  ESPE — Sistema de Gestão de Aulas
--  Schema do banco de dados (PostgreSQL / Supabase)
--  Cole TODO este arquivo no SQL Editor do Supabase e clique RUN.
-- ============================================================

-- Limpa tabelas se já existirem (seguro re-rodar)
drop table if exists aulas cascade;
drop table if exists fechamentos cascade;
drop table if exists historico_pacotes cascade;
drop table if exists alunos cascade;
drop table if exists professoras cascade;
drop table if exists pacotes cascade;

-- ---------- PROFESSORAS ----------
create table professoras (
  id           bigint generated always as identity primary key,
  nome         text not null,
  repasse_hora numeric not null default 60,
  ajuda_custo  numeric not null default 15,
  status       text not null default 'Ativa',
  pin          text not null default '0000',   -- PIN de acesso da professora
  criado_em    timestamptz default now()
);

-- ---------- PACOTES ----------
create table pacotes (
  codigo      text primary key,               -- AVULSO, PACK-6, PACK-12, PACK-20
  descricao   text not null,
  horas       numeric not null,
  valor_hora  numeric not null
);

-- ---------- ALUNOS ----------
create table alunos (
  id                 bigint generated always as identity primary key,
  nome               text not null,
  serie              text,
  materias           text,
  status             text not null default 'Ativo',
  pacote_ativo       text references pacotes(codigo),
  valor_hora         numeric not null,         -- valor histórico atual do aluno
  horas_usadas       numeric not null default 0,
  horas_contratadas  numeric not null default 0,
  responsavel        text,                     -- nome do responsável (opcional)
  observacoes        text,
  criado_em          timestamptz default now()
);

-- ---------- HISTÓRICO DE PACOTES ----------
create table historico_pacotes (
  id            bigint generated always as identity primary key,
  aluno_id      bigint references alunos(id) on delete cascade,
  pacote        text,
  horas         numeric,
  valor_hora    numeric,
  data_inicio   date,
  data_fim      text default 'em uso',
  observacoes   text
);

-- ---------- AULAS ----------
create table aulas (
  id               bigint generated always as identity primary key,
  data             date not null,
  mes              text,
  semana           int,
  aluno_id         bigint references alunos(id),
  professora_id    bigint references professoras(id),
  horario          text,
  duracao          numeric not null default 1,
  rep_hora         numeric not null,           -- repasse/hora aplicado
  rep_ajuda        numeric not null default 15,
  total_repasse    numeric not null,           -- rep_hora*duracao + rep_ajuda
  valor_aula       numeric not null,           -- valor que a família paga (histórico)
  status_pagamento text not null default 'Pendente',  -- Pendente / Pago
  recebido_em      date,                        -- data em que a família pagou
  observacoes      text,
  criado_em        timestamptz default now()
);

-- ---------- FECHAMENTOS (repasse por professora/mês) ----------
create table fechamentos (
  id             bigint generated always as identity primary key,
  professora_id  bigint references professoras(id),
  mes            text not null,                -- ex: 'Abril 2026'
  fechado        boolean not null default false,
  fechado_em     timestamptz,
  total_aulas    int,
  total_horas    numeric,
  total_repasse  numeric,
  total_ajuda    numeric,
  total          numeric,
  unique(professora_id, mes)
);

-- ---------- ÍNDICES ----------
create index idx_aulas_prof  on aulas(professora_id);
create index idx_aulas_aluno on aulas(aluno_id);
create index idx_aulas_mes   on aulas(mes);

-- ============================================================
-- Observação sobre segurança (RLS):
-- Para o protótipo, o app acessa o banco com a chave de serviço
-- guardada nos Secrets do Streamlit (nunca no código público).
-- O controle de quem vê o quê é feito DENTRO do app, por papel
-- (gestora x professora). Por isso deixamos RLS desligado aqui.
-- Se um dia quiser abrir o banco a terceiros, ative RLS e crie
-- políticas por professora.
-- ============================================================
