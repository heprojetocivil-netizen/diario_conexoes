import streamlit as st
from groq import Groq
from datetime import datetime
import json

st.set_page_config(page_title="Diário de Conexões", page_icon="💫", layout="wide")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
.stApp { background-color:#0F0F1A; font-family:'Inter',sans-serif; }
[data-testid="stSidebar"] { display:none; }
.stTextInput>div>div>input, .stTextArea>div>textarea,
.stSelectbox>div>div>div, .stNumberInput>div>div>input {
    background-color:#1A1A2E !important; color:#E2E8F0 !important;
    border:1px solid #334155 !important; font-family:'Inter',sans-serif !important;
}
.stButton>button {
    width:100%; border-radius:10px; height:3.2em;
    background:linear-gradient(135deg,#7C3AED,#A855F7) !important; color:white !important;
    font-weight:600; border:none; box-shadow:2px 2px 12px rgba(124,58,237,0.3);
    font-family:'Inter',sans-serif !important; transition:all 0.2s ease;
}
.stButton>button:hover { background:linear-gradient(135deg,#A855F7,#7C3AED) !important; transform:translateY(-1px); }
.stApp .stButton>button, .stApp .stButton>button p,
.stApp .stButton>button span, .stApp .stButton>button div { color:white !important; }
.stApp h1, .stApp h2, .stApp h3 { color:#E2E8F0 !important; font-family:'Inter',sans-serif !important; font-weight:700 !important; }
.stApp label, .stApp p, .stApp div { color:#CBD5E1 !important; }
.card { background:linear-gradient(135deg,#1E1E3A,#252542); padding:20px; border-radius:14px; border:1px solid #334155; margin-bottom:14px; }
.stApp .card, .stApp .card p, .stApp .card div, .stApp .card span { color:#E2E8F0 !important; }
.card-perfil { background:linear-gradient(135deg,#1E1A35,#2D1F4E); padding:20px; border-radius:14px; border:1px solid #7C3AED; margin-bottom:12px; cursor:pointer; }
.stApp .card-perfil, .stApp .card-perfil p, .stApp .card-perfil div { color:#E2E8F0 !important; }
.card-interacao { background:#1A1A2E; padding:16px; border-radius:12px; border-left:4px solid #A855F7; margin-bottom:10px; }
.stApp .card-interacao, .stApp .card-interacao p, .stApp .card-interacao div { color:#E2E8F0 !important; }
.card-ia { background:linear-gradient(135deg,#1A1A35,#1E2A45); padding:20px; border-radius:14px; border:1px solid #3B82F6; margin-bottom:14px; white-space:pre-wrap; }
.stApp .card-ia, .stApp .card-ia p, .stApp .card-ia div { color:#E2E8F0 !important; }
.badge { background:#7C3AED; color:white !important; padding:3px 10px; border-radius:20px; font-size:0.75em; font-weight:600; display:inline-block; margin:2px; }
.badge-verde { background:#059669; color:white !important; padding:3px 10px; border-radius:20px; font-size:0.75em; font-weight:600; display:inline-block; margin:2px; }
.badge-amarelo { background:#B45309; color:white !important; padding:3px 10px; border-radius:20px; font-size:0.75em; font-weight:600; display:inline-block; margin:2px; }
.badge-vermelho { background:#DC2626; color:white !important; padding:3px 10px; border-radius:20px; font-size:0.75em; font-weight:600; display:inline-block; margin:2px; }
.divider { border:none; height:1px; background:linear-gradient(to right,transparent,#7C3AED,transparent); margin:18px 0; }
.stat-box { background:#1A1A2E; border-radius:12px; padding:16px; text-align:center; border:1px solid #334155; }
.stApp .stat-box div, .stApp .stat-box span { color:#E2E8F0 !important; }
.nome-destaque { font-size:1.3em; font-weight:700; color:#C084FC !important; }
.tag-tipo { font-size:0.8em; color:#94A3B8 !important; }
</style>
""", unsafe_allow_html=True)

SYSTEM_PROMPT = (
    "Você é um conselheiro discreto e perspicaz especialista em dinâmicas relacionais e comportamento humano. "
    "Analisa padrões de interação, sinais de interesse, linguagem não-verbal e compatibilidade emocional. "
    "Dá insights práticos, honestos e diretos. Responde sempre em Português do Brasil."
)

def carregar_json_sessao(dados):
    import re as _re
    _bloq = {'api_key','etapa','nome_login','chave_login','upload_login','btn_entrar_login'}
    _pref = ('btn_','sel_','ul_','dl_','_sub','_sm','_tab','nav_',)
    for k, v in dados.items():
        if k in _bloq: continue
        if any(k.startswith(p) for p in _pref): continue
        if _re.match(r'.+_\d+$', k): continue
        st.session_state[k] = v

defaults = {
    "etapa": "Login",
    "usuario": "",
    "api_key": "",
    "conexoes": {},       # {nome: {perfil, interacoes, analise_ia}}
    "conexao_ativa": None,
    "pagina": "Lista",
}
for k, v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v

def chamar_ia(prompt: str) -> str:
    try:
        client = Groq(api_key=st.session_state.api_key)
        resp = client.chat.completions.create(
            messages=[{"role":"system","content":SYSTEM_PROMPT},{"role":"user","content":prompt}],
            model="openai/gpt-oss-120b", max_tokens=2048
        )
        return resp.choices[0].message.content or ""
    except Exception as e:
        st.error(f"Erro na API: {e}")
        return ""

def salvar_conexao(nome, perfil):
    if nome not in st.session_state.conexoes:
        st.session_state.conexoes[nome] = {"perfil": perfil, "interacoes": [], "analise_ia": ""}
    else:
        st.session_state.conexoes[nome]["perfil"] = perfil

def get_badge_tipo(tipo):
    cores = {
        "Amizade": "badge-verde",
        "Interesse romântico": "badge",
        "Relacionamento": "badge",
        "Ficante": "badge-amarelo",
        "Ex": "badge-vermelho",
        "Colega": "badge-verde",
        "Outro": "badge-amarelo",
    }
    return cores.get(tipo, "badge")

# ── LOGIN ──
if st.session_state.etapa == "Login":
    st.markdown("# 💫 Diário de Conexões")
    st.markdown("<div class='card'>Registre, acompanhe e entenda as mulheres na sua vida com apoio de IA.</div>", unsafe_allow_html=True)
    nome  = st.text_input("Seu Nome:", key="nome_login")
    chave = st.text_input("🔑 Chave API da Groq:", type="password", key="chave_login")
    arq_j = st.file_uploader("📂 Carregar dados salvos (.json):", type=["json"], key="upload_login")
    if arq_j:
        try:
            carregar_json_sessao(json.load(arq_j))
        except: pass
    if st.button("✨ ENTRAR", key="btn_entrar_login"):
        if len(nome.strip()) < 2:
            st.warning("Digite um nome com pelo menos 2 caracteres.")
        elif chave.strip():
            st.session_state.usuario = nome.strip()
            st.session_state.api_key = chave.strip()
            st.session_state.etapa = "App"
            st.rerun()
        else:
            st.warning("Preencha nome e chave API.")

elif st.session_state.etapa == "App":
    usuario = st.session_state.usuario

    # ── HEADER ──
    st.markdown(f"# 💫 Diário de Conexões")
    st.markdown(f"<div style='color:#94A3B8;margin-bottom:8px;'>Olá, <b style='color:#C084FC'>{usuario}</b> — {len(st.session_state.conexoes)} conexão(ões) registrada(s)</div>", unsafe_allow_html=True)

    # ── SALVAR ──
    with st.expander("💾 Salvar / Carregar dados", expanded=False):
        _bs1, _bs2 = st.columns(2)
        with _bs1:
            _dsv = {k: st.session_state.get(k) for k in list(st.session_state.keys()) if not k.startswith("_") and k != "api_key"}
            st.download_button("💾 Baixar dados (.json)",
                data=json.dumps(_dsv, ensure_ascii=False, indent=2, default=str),
                file_name=f"conexoes_{usuario}.json",
                mime="application/json", key="dl_sv_dc")
        with _bs2:
            _fup = st.file_uploader("📂 Carregar:", type=["json"], key="ul_sv_dc", label_visibility="collapsed")
            if _fup:
                try:
                    for _k, _v in json.loads(_fup.read().decode()).items():
                        if _k not in ("api_key","etapa"): st.session_state[_k] = _v
                    st.success("✅ Restaurado!"); st.rerun()
                except: st.error("Arquivo inválido.")

    st.markdown("<hr class='divider'>", unsafe_allow_html=True)

    # ── NAVEGAÇÃO ──
    _pgs = ["📋 Lista de Conexões", "➕ Nova Conexão", "👤 Perfil & Interações", "📅 Encontros Futuros", "🤖 Análise IA"]
    _pg_map = {"Lista":0,"Nova":1,"Perfil":2,"Futuros":3,"IA":4}
    _sel = st.selectbox("", _pgs,
        index=_pg_map.get(st.session_state.pagina, 0),
        key="nav_dc", label_visibility="collapsed")

    if "Lista" in _sel: st.session_state.pagina = "Lista"
    elif "Nova" in _sel: st.session_state.pagina = "Nova"
    elif "Perfil" in _sel: st.session_state.pagina = "Perfil"
    elif "Futuros" in _sel: st.session_state.pagina = "Futuros"
    elif "Análise" in _sel: st.session_state.pagina = "IA"

    st.markdown("<hr class='divider'>", unsafe_allow_html=True)

    # ══════════════════════════════════
    # 📋 LISTA DE CONEXÕES
    # ══════════════════════════════════
    if st.session_state.pagina == "Lista":
        st.header("📋 Suas Conexões")

        if not st.session_state.conexoes:
            st.markdown("<div class='card' style='text-align:center;'><div style='font-size:3em;'>💫</div><div>Nenhuma conexão registrada ainda.<br>Use <b>➕ Nova Conexão</b> para começar.</div></div>", unsafe_allow_html=True)
        else:
            # Filtro
            _tipos_exist = list(set(c["perfil"].get("tipo_relacao","") for c in st.session_state.conexoes.values()))
            _filtro = st.selectbox("Filtrar por tipo:", ["Todas"] + sorted(_tipos_exist), key="sel_filtro_lista")

            for nome, dados in st.session_state.conexoes.items():
                p = dados["perfil"]
                if _filtro != "Todas" and p.get("tipo_relacao","") != _filtro:
                    continue
                tipo = p.get("tipo_relacao","?")
                badge_cls = get_badge_tipo(tipo)
                n_inter = len(dados.get("interacoes",[]))
                bairro = p.get("bairro","")
                idade = p.get("idade","")
                interesse = p.get("interesse_dela","")[:60] + "..." if len(p.get("interesse_dela","")) > 60 else p.get("interesse_dela","")

                col_info, col_btn = st.columns([4,1])
                with col_info:
                    st.markdown(
                        f"<div class='card-perfil'>"
                        f"<span class='nome-destaque'>{nome}</span> "
                        f"<span class='{badge_cls}'>{tipo}</span>"
                        f"<span class='badge-amarelo' style='margin-left:6px;'>{n_inter} interação(ões)</span><br>"
                        f"<span class='tag-tipo'>📍 {bairro} · {idade} anos</span><br>"
                        f"<span style='font-size:0.85em;color:#94A3B8;'>💭 {interesse}</span>"
                        f"</div>",
                        unsafe_allow_html=True
                    )
                with col_btn:
                    st.markdown("<br>", unsafe_allow_html=True)
                    if st.button("Ver →", key=f"btn_ver_{nome}"):
                        st.session_state.conexao_ativa = nome
                        st.session_state.pagina = "Perfil"
                        st.rerun()

    # ══════════════════════════════════
    # ➕ NOVA CONEXÃO
    # ══════════════════════════════════
    elif st.session_state.pagina == "Nova":
        st.header("➕ Nova Conexão")
        st.markdown("Registre o perfil desta mulher na sua vida.")
        st.markdown("<hr class='divider'>", unsafe_allow_html=True)

        # Se está editando uma existente
        _editando = st.session_state.get("editando_conexao", None)
        _perfil_atual = st.session_state.conexoes.get(_editando, {}).get("perfil", {}) if _editando else {}

        c1, c2 = st.columns(2)
        with c1:
            nome_novo = st.text_input("Nome (ou apelido):",
                value=_perfil_atual.get("nome", ""),
                key="inp_nome_novo",
                placeholder="Ex: Ana, Ju do Trabalho...")
            idade_nova = st.number_input("Idade:", min_value=18, max_value=80,
                value=int(_perfil_atual.get("idade", 25)), key="inp_idade_nova")
            bairro_novo = st.text_input("Bairro / Cidade:",
                value=_perfil_atual.get("bairro", ""),
                key="inp_bairro_novo",
                placeholder="Ex: Moema, São Paulo")
        with c2:
            tipo_rel = st.selectbox("Tipo de relação:",
                ["Interesse romântico","Ficante","Relacionamento","Amizade","Ex","Colega","Outro"],
                index=["Interesse romântico","Ficante","Relacionamento","Amizade","Ex","Colega","Outro"].index(
                    _perfil_atual.get("tipo_relacao","Interesse romântico")),
                key="sel_tipo_rel")
            como_conheceu = st.selectbox("Como se conheceram?",
                ["Pessoalmente","App de relacionamento","Redes sociais","Trabalho/faculdade","Amigos em comum","Balada/evento","Outro"],
                index=["Pessoalmente","App de relacionamento","Redes sociais","Trabalho/faculdade","Amigos em comum","Balada/evento","Outro"].index(
                    _perfil_atual.get("como_conheceu","Pessoalmente")),
                key="sel_como_conheceu")
            status_atual = st.selectbox("Status atual:",
                ["Ativa — estou em contato","Pausada — sem contato recente","Encerrada","Indefinida"],
                index=["Ativa — estou em contato","Pausada — sem contato recente","Encerrada","Indefinida"].index(
                    _perfil_atual.get("status_atual","Ativa — estou em contato")),
                key="sel_status_atual")

        st.markdown("**O interesse dela em você:**")
        interesse_dela = st.text_area("O que ela esperava de você? O que demonstrou querer?",
            height=100, key="ta_interesse_dela",
            value=_perfil_atual.get("interesse_dela",""),
            placeholder="Ex: ela queria algo sério, parecia interessada em sair, mandava mensagem todos os dias...")

        st.markdown("**Sua atitude e como ela reagiu:**")
        c3, c4 = st.columns(2)
        with c3:
            sua_atitude = st.text_area("O que você demonstrou / como agiu:",
                height=90, key="ta_sua_atitude",
                value=_perfil_atual.get("sua_atitude",""),
                placeholder="Ex: fui direto, dei muito espaço, fui muito disponível...")
        with c4:
            reacao_dela = st.text_area("Como ela interpretou / reagiu:",
                height=90, key="ta_reacao_dela",
                value=_perfil_atual.get("reacao_dela",""),
                placeholder="Ex: achou que eu não tinha interesse, ficou animada, se afastou...")

        st.markdown("**Personalidade e características:**")
        c5, c6 = st.columns(2)
        with c5:
            personalidade = st.multiselect("Perfil dela:",
                ["Extrovertida","Introvertida","Independente","Carente","Comunicativa","Reservada",
                 "Ambiciosa","Romântica","Divertida","Séria","Ciúmenta","Desapegada","Intensa","Leve"],
                default=_perfil_atual.get("personalidade",[]),
                key="ms_personalidade")
        with c6:
            nivel_interesse = st.select_slider("Nível de interesse dela em você (1–10):",
                options=list(range(1,11)),
                value=_perfil_atual.get("nivel_interesse",5),
                key="sl_nivel_interesse")
            nivel_seu = st.select_slider("Seu nível de interesse nela (1–10):",
                options=list(range(1,11)),
                value=_perfil_atual.get("nivel_seu",5),
                key="sl_nivel_seu")

        obs_perfil = st.text_area("Observações adicionais (opcional):",
            height=80, key="ta_obs_perfil",
            value=_perfil_atual.get("obs_perfil",""),
            placeholder="Qualquer detalhe importante que queira lembrar...")

        if st.button("💾 SALVAR PERFIL", key="btn_salvar_perfil", use_container_width=True):
            if not nome_novo.strip():
                st.warning("Digite um nome.")
            else:
                _nome_key = nome_novo.strip()
                _perfil = {
                    "nome": _nome_key,
                    "idade": idade_nova,
                    "bairro": bairro_novo,
                    "tipo_relacao": tipo_rel,
                    "como_conheceu": como_conheceu,
                    "status_atual": status_atual,
                    "interesse_dela": interesse_dela,
                    "sua_atitude": sua_atitude,
                    "reacao_dela": reacao_dela,
                    "personalidade": personalidade,
                    "nivel_interesse": nivel_interesse,
                    "nivel_seu": nivel_seu,
                    "obs_perfil": obs_perfil,
                    "data_registro": datetime.now().strftime("%d/%m/%Y"),
                }
                salvar_conexao(_nome_key, _perfil)
                if _editando and _editando != _nome_key:
                    # renomear
                    st.session_state.conexoes[_nome_key] = st.session_state.conexoes.pop(_editando)
                st.session_state.editando_conexao = None
                st.session_state.conexao_ativa = _nome_key
                st.session_state.pagina = "Perfil"
                st.success(f"✅ {_nome_key} salva!")
                st.rerun()

    # ══════════════════════════════════
    # 👤 PERFIL & INTERAÇÕES
    # ══════════════════════════════════
    elif st.session_state.pagina == "Perfil":

        if not st.session_state.conexoes:
            st.info("Nenhuma conexão registrada. Crie uma primeiro.")
        else:
            # Seletor de conexão
            nomes = list(st.session_state.conexoes.keys())
            _idx = nomes.index(st.session_state.conexao_ativa) if st.session_state.conexao_ativa in nomes else 0
            _nome_sel = st.selectbox("Selecionar conexão:", nomes, index=_idx, key="sel_conexao_ativa")
            if _nome_sel != st.session_state.conexao_ativa:
                st.session_state.conexao_ativa = _nome_sel
                st.rerun()

            nome_c = st.session_state.conexao_ativa
            dados_c = st.session_state.conexoes[nome_c]
            p = dados_c["perfil"]

            # Cabeçalho do perfil
            badge_cls = get_badge_tipo(p.get("tipo_relacao",""))
            st.markdown(f"""
            <div class='card'>
            <div style='display:flex;justify-content:space-between;align-items:flex-start;flex-wrap:wrap;gap:8px;'>
              <div>
                <div style='font-size:1.6em;font-weight:700;color:#C084FC;'>{nome_c}</div>
                <span class='{badge_cls}'>{p.get('tipo_relacao','')}</span>
                <span class='badge-amarelo'>{p.get('status_atual','')}</span>
              </div>
              <div style='text-align:right;'>
                <div style='color:#94A3B8;font-size:0.85em;'>📍 {p.get('bairro','')} · {p.get('idade','')} anos</div>
                <div style='color:#94A3B8;font-size:0.85em;'>🤝 {p.get('como_conheceu','')}</div>
                <div style='color:#94A3B8;font-size:0.85em;'>📅 Registrada em {p.get('data_registro','')}</div>
              </div>
            </div>
            <hr style='border-color:#334155;margin:12px 0;'>
            <div style='display:grid;grid-template-columns:1fr 1fr;gap:12px;'>
              <div><b style='color:#C084FC;'>Interesse dela:</b><br>{p.get('interesse_dela','—')}</div>
              <div><b style='color:#C084FC;'>Sua atitude:</b><br>{p.get('sua_atitude','—')}</div>
              <div><b style='color:#C084FC;'>Reação dela:</b><br>{p.get('reacao_dela','—')}</div>
              <div><b style='color:#C084FC;'>Personalidade:</b><br>{', '.join(p.get('personalidade',[])) or '—'}</div>
            </div>
            <hr style='border-color:#334155;margin:12px 0;'>
            <div style='display:flex;gap:20px;'>
              <div>⭐ Interesse dela: <b>{p.get('nivel_interesse','-')}/10</b></div>
              <div>💜 Seu interesse: <b>{p.get('nivel_seu','-')}/10</b></div>
            </div>
            {f"<div style='color:#94A3B8;font-size:0.85em;margin-top:8px;'>📝 {p.get('obs_perfil','')}</div>" if p.get('obs_perfil') else ''}
            </div>
            """, unsafe_allow_html=True)

            # Botões de ação
            ca1, ca2, ca3 = st.columns(3)
            with ca1:
                if st.button("✏️ Editar Perfil", key="btn_editar_perfil"):
                    st.session_state.editando_conexao = nome_c
                    st.session_state.pagina = "Nova"
                    st.rerun()
            with ca2:
                if st.button("🤖 Análise IA", key="btn_ir_ia"):
                    st.session_state.pagina = "IA"
                    st.rerun()
            with ca3:
                if st.button("🗑️ Excluir Conexão", key="btn_excluir"):
                    del st.session_state.conexoes[nome_c]
                    st.session_state.conexao_ativa = list(st.session_state.conexoes.keys())[0] if st.session_state.conexoes else None
                    st.session_state.pagina = "Lista"
                    st.rerun()

            st.markdown("<hr class='divider'>", unsafe_allow_html=True)

            # ── REGISTRAR NOVA INTERAÇÃO ──
            st.subheader("➕ Registrar Interação")
            ci1, ci2 = st.columns(2)
            with ci1:
                data_inter = st.date_input("Data da interação:", key="di_data")
                tipo_inter = st.selectbox("Tipo de interação:",
                    ["Conversa presencial","Mensagem/chat","Chamada/vídeo","Saída / encontro","Indireto (viu ela, soube algo)","Outro"],
                    key="sel_tipo_inter")
                humor_dela = st.radio("Humor dela:",
                    ["😊 Positivo","😐 Neutro","😒 Distante","😡 Negativo","😍 Muito positivo"],
                    horizontal=True, key="rad_humor_dela")
            with ci2:
                iniciativa = st.radio("Quem tomou iniciativa?",
                    ["Eu","Ela","Os dois","Nenhum"],
                    horizontal=True, key="rad_iniciativa")
                seu_humor = st.radio("Seu estado nessa interação:",
                    ["😎 Confiante","😊 Tranquilo","😅 Nervoso","😔 Inseguro"],
                    horizontal=True, key="rad_seu_humor")
                nivel_conexao = st.select_slider("Nível de conexão sentido (1–10):",
                    options=list(range(1,11)), value=5, key="sl_nivel_conexao")

            como_ela_agiu = st.text_area("Como ela agiu nessa interação:",
                height=80, key="ta_como_ela_agiu",
                placeholder="Ex: foi carinhosa, ficou fria, mandou mensagem primeiro, fez contato visual...")
            como_eu_agi = st.text_area("Como você agiu / o que demonstrou:",
                height=80, key="ta_como_eu_agi",
                placeholder="Ex: fui direto e marquei um encontro, fiquei ansioso, me mostrei interessado...")
            o_que_aprendi = st.text_area("O que você aprendeu ou percebeu nessa interação:",
                height=70, key="ta_o_que_aprendi",
                placeholder="Ex: ela gosta quando sou mais direto, preciso dar menos atenção gratuita...")

            if st.button("💾 SALVAR INTERAÇÃO", key="btn_salvar_inter", use_container_width=True):
                if not como_ela_agiu.strip() and not como_eu_agi.strip():
                    st.warning("Descreva ao menos como ela ou você agiu.")
                else:
                    _inter = {
                        "data": data_inter.strftime("%d/%m/%Y"),
                        "tipo": tipo_inter,
                        "humor_dela": humor_dela,
                        "iniciativa": iniciativa,
                        "seu_humor": seu_humor,
                        "nivel_conexao": nivel_conexao,
                        "como_ela_agiu": como_ela_agiu,
                        "como_eu_agi": como_eu_agi,
                        "o_que_aprendi": o_que_aprendi,
                        "id": datetime.now().strftime("%Y%m%d%H%M%S"),
                    }
                    st.session_state.conexoes[nome_c]["interacoes"].append(_inter)
                    st.success("✅ Interação registrada!"); st.rerun()

            # ── HISTÓRICO DE INTERAÇÕES ──
            interacoes = dados_c.get("interacoes", [])
            if interacoes:
                st.markdown("<hr class='divider'>", unsafe_allow_html=True)
                st.subheader(f"📅 Histórico ({len(interacoes)} interação(ões))")
                for i, inter in enumerate(reversed(interacoes)):
                    with st.expander(f"{inter['data']} — {inter['tipo']} · conexão {inter.get('nivel_conexao','-')}/10 {inter['humor_dela'].split(' ')[0]}", expanded=(i==0)):
                        ch1, ch2 = st.columns(2)
                        with ch1:
                            st.markdown(f"**Iniciativa:** {inter.get('iniciativa','')}")
                            st.markdown(f"**Humor dela:** {inter.get('humor_dela','')}")
                            st.markdown(f"**Seu estado:** {inter.get('seu_humor','')}")
                        with ch2:
                            st.markdown(f"**Conexão:** {inter.get('nivel_conexao','-')}/10")
                        if inter.get("como_ela_agiu"):
                            st.markdown(f"**Como ela agiu:** {inter['como_ela_agiu']}")
                        if inter.get("como_eu_agi"):
                            st.markdown(f"**Como você agiu:** {inter['como_eu_agi']}")
                        if inter.get("o_que_aprendi"):
                            st.markdown(f"**Aprendizado:** {inter['o_que_aprendi']}")
                        if st.button("🗑️ Excluir", key=f"btn_del_inter_{inter['id']}"):
                            st.session_state.conexoes[nome_c]["interacoes"] = [
                                x for x in interacoes if x["id"] != inter["id"]
                            ]
                            st.rerun()

    # ══════════════════════════════════
    # 📅 ENCONTROS FUTUROS — CHAT IA
    # ══════════════════════════════════
    elif st.session_state.pagina == "Futuros":
        st.header("📅 Encontros Futuros")
        st.markdown(
            "<div style='color:#94A3B8;margin-bottom:16px;'>"
            "Conta o que está acontecendo e a IA te dá dicas em tempo real para o seu próximo encontro."
            "</div>", unsafe_allow_html=True
        )

        if not st.session_state.conexoes:
            st.info("Nenhuma conexão registrada. Crie uma primeiro.")
        else:
            # Inicializar chat por conexão
            if "chat_futuros" not in st.session_state:
                st.session_state.chat_futuros = {}   # {nome: [{role, content}]}

            nomes_cx = list(st.session_state.conexoes.keys())
            ef_nome = st.selectbox("Com quem é o encontro?", nomes_cx, key="sel_ef_nome")

            p_ef = st.session_state.conexoes.get(ef_nome, {}).get("perfil", {})
            inter_ef = st.session_state.conexoes.get(ef_nome, {}).get("interacoes", [])

            # Montar contexto do perfil para a IA
            hist_inter = ""
            for ix in inter_ef[-4:]:
                hist_inter += (
                    f"- {ix['data']} ({ix['tipo']}): ela {ix.get('como_ela_agiu','')[:70]} / "
                    f"eu {ix.get('como_eu_agi','')[:70]} | conexão {ix.get('nivel_conexao','-')}/10\n"
                )
            _ctx_perfil = (
                f"PERFIL DE {ef_nome.upper()}:\n"
                f"- Tipo de relação: {p_ef.get('tipo_relacao','')}\n"
                f"- Idade: {p_ef.get('idade','')} | Bairro: {p_ef.get('bairro','')}\n"
                f"- Como se conheceram: {p_ef.get('como_conheceu','')}\n"
                f"- Status: {p_ef.get('status_atual','')}\n"
                f"- O que ela quer: {p_ef.get('interesse_dela','')}\n"
                f"- Minha atitude com ela: {p_ef.get('sua_atitude','')}\n"
                f"- Como ela reagiu: {p_ef.get('reacao_dela','')}\n"
                f"- Personalidade: {', '.join(p_ef.get('personalidade', []))}\n"
                f"- Interesse dela em mim: {p_ef.get('nivel_interesse','-')}/10\n"
                f"- Meu interesse: {p_ef.get('nivel_seu','-')}/10\n"
                f"HISTÓRICO DE INTERAÇÕES (últimas 4):\n"
                f"{hist_inter or 'Nenhuma interação registrada ainda.'}\n\n"
                f"Você é um coach de relacionamentos. Use esse contexto para dar conselhos práticos, "
                f"diretos e personalizados sobre o próximo encontro. Responda em Português do Brasil."
            )

            # Inicializar chat desta conexão
            if ef_nome not in st.session_state.chat_futuros:
                st.session_state.chat_futuros[ef_nome] = []

            historico = st.session_state.chat_futuros[ef_nome]

            # Mostrar card de contexto carregado
            st.markdown(
                f"<div class='card' style='border-color:#7C3AED;padding:14px;margin-bottom:12px;'>"
                f"<span style='color:#C084FC;font-weight:700;'>🧠 Contexto carregado:</span> "
                f"<b>{ef_nome}</b> · {p_ef.get('tipo_relacao','')} · {p_ef.get('idade','')} anos · "
                f"Interesse dela {p_ef.get('nivel_interesse','-')}/10 · {len(inter_ef)} interação(ões) registrada(s)"
                f"</div>", unsafe_allow_html=True
            )

            # Exibir histórico do chat
            if not historico:
                st.markdown(
                    "<div class='card' style='text-align:center;padding:24px;'>"
                    "<div style='font-size:2em;'>💬</div>"
                    "<div style='color:#94A3B8;margin-top:8px;'>Conta o que está rolando com ela.<br>"
                    "Ex: <i>\"Vou encontrá-la amanhã à noite num bar, ela parece interessada mas fica quente e fria...\"</i></div>"
                    "</div>", unsafe_allow_html=True
                )
            else:
                for msg in historico:
                    if msg["role"] == "user":
                        st.markdown(
                            f"<div style='background:#1E2A45;border-radius:12px;padding:12px 16px;"
                            f"margin:6px 0;border-left:3px solid #3B82F6;'>"
                            f"<span style='color:#60A5FA;font-size:0.8em;font-weight:600;'>VOCÊ</span><br>"
                            f"<span style='color:#E2E8F0;'>{msg['content']}</span></div>",
                            unsafe_allow_html=True
                        )
                    else:
                        st.markdown(
                            f"<div style='background:#1A1A35;border-radius:12px;padding:12px 16px;"
                            f"margin:6px 0;border-left:3px solid #A855F7;'>"
                            f"<span style='color:#C084FC;font-size:0.8em;font-weight:600;'>🤖 COACH IA</span><br>"
                            f"<span style='color:#E2E8F0;white-space:pre-wrap;'>{msg['content']}</span></div>",
                            unsafe_allow_html=True
                        )

            st.markdown("<br>", unsafe_allow_html=True)

            # Input do usuário
            _msg_usr = st.text_area(
                "O que está acontecendo? O que você quer saber?",
                height=100,
                key="ta_ef_chat_input",
                placeholder=(
                    "Ex: Vou buscá-la em casa às 20h, ela confirmou mas demorou para responder. "
                    "Estou com dúvida se devo beijá-la logo ou esperar mais. O que você acha?"
                )
            )

            c_btn1, c_btn2 = st.columns([3, 1])
            with c_btn1:
                _enviar = st.button("📨 ENVIAR E RECEBER DICA", key="btn_ef_enviar", use_container_width=True)
            with c_btn2:
                if st.button("🗑️ Limpar chat", key="btn_ef_limpar", use_container_width=True):
                    st.session_state.chat_futuros[ef_nome] = []
                    st.rerun()

            if _enviar and _msg_usr.strip():
                # Adicionar mensagem do usuário
                historico.append({"role": "user", "content": _msg_usr.strip()})

                # Montar histórico para a API
                msgs_api = [{"role": "system", "content": _ctx_perfil}]
                for m in historico:
                    msgs_api.append({"role": m["role"], "content": m["content"]})

                with st.spinner("🤖 Pensando nas melhores dicas..."):
                    try:
                        client = Groq(api_key=st.session_state.api_key)
                        resp = client.chat.completions.create(
                            messages=msgs_api,
                            model="openai/gpt-oss-120b",
                            max_tokens=1024
                        )
                        resposta = resp.choices[0].message.content or ""
                        if resposta:
                            historico.append({"role": "assistant", "content": resposta})
                            st.session_state.chat_futuros[ef_nome] = historico
                    except Exception as e:
                        st.error(f"Erro na API: {e}")

                st.rerun()

    # ══════════════════════════════════
    # 🤖 ANÁLISE IA
    # ══════════════════════════════════
    elif st.session_state.pagina == "IA":
        st.header("🤖 Análise IA")

        if not st.session_state.conexoes:
            st.info("Nenhuma conexão registrada ainda.")
        else:
            nomes = list(st.session_state.conexoes.keys())
            _idx = nomes.index(st.session_state.conexao_ativa) if st.session_state.conexao_ativa in nomes else 0
            _nome_ia = st.selectbox("Analisar conexão:", nomes, index=_idx, key="sel_ia_nome")
            if _nome_ia != st.session_state.conexao_ativa:
                st.session_state.conexao_ativa = _nome_ia

            nome_c = _nome_ia
            dados_c = st.session_state.conexoes[nome_c]
            p = dados_c["perfil"]
            interacoes = dados_c.get("interacoes", [])

            tipo_analise = st.selectbox("Que tipo de análise você quer?",
                ["📊 Análise geral do padrão de interação",
                 "💭 O que ela realmente sente por mim?",
                 "🎯 O que devo fazer na próxima interação?",
                 "⚠️ Erros que estou cometendo",
                 "💪 Pontos fortes meus nessa relação",
                 "🔮 Para onde essa relação está indo?",
                 "💡 Como aumentar o interesse dela?"],
                key="sel_tipo_analise")

            contexto_extra = st.text_area("Contexto adicional (opcional):",
                height=80, key="ta_contexto_ia",
                placeholder="Alguma situação recente específica que queira incluir na análise...")

            if st.button("🤖 GERAR ANÁLISE", key="btn_gerar_ia", use_container_width=True):
                # Montar histórico de interações
                hist_txt = ""
                for i, inter in enumerate(interacoes[-5:], 1):
                    hist_txt += (
                        f"\nInteração {i} ({inter['data']} — {inter['tipo']}):\n"
                        f"- Iniciativa: {inter.get('iniciativa','')}\n"
                        f"- Humor dela: {inter.get('humor_dela','')}\n"
                        f"- Nível de conexão: {inter.get('nivel_conexao','-')}/10\n"
                        f"- Como ela agiu: {inter.get('como_ela_agiu','')}\n"
                        f"- Como eu agi: {inter.get('como_eu_agi','')}\n"
                        f"- Aprendizado: {inter.get('o_que_aprendi','')}\n"
                    )

                prompt = (
                    f"Análise solicitada: {tipo_analise}\n\n"
                    f"PERFIL DA CONEXÃO:\n"
                    f"- Nome: {nome_c} | Idade: {p.get('idade','')} | Bairro: {p.get('bairro','')}\n"
                    f"- Tipo de relação: {p.get('tipo_relacao','')}\n"
                    f"- Como se conheceram: {p.get('como_conheceu','')}\n"
                    f"- Status: {p.get('status_atual','')}\n"
                    f"- Interesse dela: {p.get('interesse_dela','')}\n"
                    f"- Atitude do usuário: {p.get('sua_atitude','')}\n"
                    f"- Reação dela: {p.get('reacao_dela','')}\n"
                    f"- Personalidade: {', '.join(p.get('personalidade',[]))}\n"
                    f"- Nível de interesse dela: {p.get('nivel_interesse','-')}/10\n"
                    f"- Nível de interesse do usuário: {p.get('nivel_seu','-')}/10\n"
                    f"- Observações: {p.get('obs_perfil','')}\n\n"
                    f"HISTÓRICO DE INTERAÇÕES ({len(interacoes)} no total — últimas 5):\n"
                    f"{hist_txt if hist_txt else 'Nenhuma interação registrada ainda.'}\n\n"
                    f"CONTEXTO EXTRA: {contexto_extra or 'nenhum'}\n\n"
                    f"Faça uma análise profunda, honesta e prática. Seja direto e específico."
                )

                with st.spinner("🤖 Analisando..."):
                    resultado = chamar_ia(prompt)
                    if resultado:
                        st.session_state.conexoes[nome_c]["analise_ia"] = resultado

            if dados_c.get("analise_ia"):
                st.markdown(f"<div class='card-ia'>{dados_c['analise_ia']}</div>", unsafe_allow_html=True)
                st.download_button("📋 Baixar análise",
                    data=dados_c["analise_ia"],
                    file_name=f"analise_{nome_c}.txt",
                    mime="text/plain",
                    key="dl_analise_ia")

            # Análise comparativa de todas
            st.markdown("<hr class='divider'>", unsafe_allow_html=True)
            st.subheader("🌐 Visão Geral das Suas Conexões")
            if st.button("🤖 ANALISAR PADRÃO GERAL", key="btn_geral_ia", use_container_width=True):
                resumo_todas = ""
                for nm, dc in st.session_state.conexoes.items():
                    pp = dc["perfil"]
                    resumo_todas += (
                        f"\n— {nm} ({pp.get('tipo_relacao','')}, {pp.get('idade','')} anos, {pp.get('bairro','')}):\n"
                        f"  Interesse dela: {pp.get('nivel_interesse','-')}/10 | Seu interesse: {pp.get('nivel_seu','-')}/10\n"
                        f"  Status: {pp.get('status_atual','')} | {len(dc.get('interacoes',[]))} interação(ões)\n"
                        f"  Atitude do usuário: {pp.get('sua_atitude','')[:80]}\n"
                    )
                prompt_geral = (
                    f"Analise o padrão de comportamento deste homem nas suas relações com mulheres:\n"
                    f"{resumo_todas}\n\n"
                    f"Identifique: padrões repetitivos, pontos fortes, erros comuns, e o que ele pode mudar "
                    f"para ter melhores conexões. Seja direto e honesto."
                )
                with st.spinner("🤖 Analisando todas as conexões..."):
                    res_geral = chamar_ia(prompt_geral)
                    if res_geral:
                        st.session_state["analise_geral_dc"] = res_geral

            if st.session_state.get("analise_geral_dc"):
                st.markdown(f"<div class='card-ia'>{st.session_state['analise_geral_dc']}</div>", unsafe_allow_html=True)

# ── RODAPÉ ──
st.markdown("<hr class='divider'>", unsafe_allow_html=True)
st.markdown("<div style='text-align:center;font-size:0.75em;color:#475569;'>© 2026 Diário de Conexões · Privado e seguro</div>", unsafe_allow_html=True)
