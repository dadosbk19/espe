"""Cores, estilos e identidade visual da ESPE — reutilizados no app e nos PDFs."""

# Paleta oficial ESPE
VERDE   = "#acc900"
AZUL    = "#516ed6"
AMARELO = "#f9bf41"
CORAL   = "#e96e4c"
LILAS   = "#cd89ff"
CREME   = "#f9eedc"
TINTA   = "#2a2a3c"
CINZA   = "#6b6b7d"
OK      = "#3aaf6b"

CSS = f"""
<style>
.stApp {{ background:{CREME}; }}
/* logo */
.espe-logo {{ font-size:34px; font-weight:800; letter-spacing:-1px; line-height:1; }}
.espe-logo .e {{ color:{CORAL}; }} .espe-logo .s {{ color:{AMARELO}; }}
.espe-logo .p {{ color:{AZUL}; }}  .espe-logo .e2 {{ color:{VERDE}; }}
.espe-sub {{ font-size:10px; font-weight:600; color:{CINZA}; letter-spacing:.5px; }}
/* kpi cards */
.kpi {{ background:#fff; border-radius:16px; padding:16px 18px; border-left:5px solid {AZUL}; }}
.kpi .lbl {{ font-size:11px; font-weight:700; color:{CINZA}; text-transform:uppercase; letter-spacing:.4px; }}
.kpi .val {{ font-size:25px; font-weight:800; color:{TINTA}; }}
.kpi .dlt {{ font-size:12px; color:{CINZA}; }}
/* alerts */
.alert {{ padding:12px 16px; border-radius:13px; margin-bottom:9px; font-size:14px; }}
.alert.warn {{ background:#e96e4c14; border-left:4px solid {CORAL}; }}
.alert.info {{ background:#f9bf4118; border-left:4px solid {AMARELO}; }}
/* fechado banner (professora) */
.fechado {{ background:linear-gradient(120deg,{AZUL},{LILAS}); color:#fff;
  border-radius:18px; padding:22px 26px; }}
.fechado .v {{ font-size:36px; font-weight:800; margin:4px 0; }}
.aguardando {{ background:{CREME}; border:2px dashed {AMARELO}; border-radius:16px;
  padding:28px; text-align:center; color:{CINZA}; }}
/* botoes */
.stButton>button {{ border-radius:12px; font-weight:700; border:none; }}
section[data-testid="stSidebar"] {{ background:#fff; }}
</style>
"""

LOGO_HTML = """
<div class="espe-logo"><span class="e">E</span><span class="s">S</span><span class="p">P</span><span class="e2">E</span></div>
<div class="espe-sub">educação sensorial personalizada</div>
"""
