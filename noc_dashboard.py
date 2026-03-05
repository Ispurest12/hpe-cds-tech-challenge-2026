import streamlit as st
import json
import os
import time
import base64


# --- FUNCIÓN VISOR 3D ---
def visor_3d_glb(archivo):
    try:
        if os.path.exists(archivo):
            with open(archivo, "rb") as f:
                data = base64.b64encode(f.read()).decode()
            html_3d = f'''
            <script type="module" src="https://unpkg.com/@google/model-viewer/dist/model-viewer.min.js"></script>
            <model-viewer src="data:model/gltf-binary;base64,{data}" 
                          alt="Topología Nodo Edge" auto-rotate camera-controls 
                          style="width: 100%; height: 350px; background-color: #0b0f19; border-radius: 10px; border: 1px solid #00d4ff;">
            </model-viewer>
            '''
            st.components.v1.html(html_3d, height=360)
        else:
            st.error(f"Archivo de topología no encontrado: {archivo}")
    except Exception as e:
        st.error(f"Error al renderizar gemelo digital: {e}")


def aplicar_marca_agua(ruta_logo):
    if os.path.exists(ruta_logo):
        with open(ruta_logo, "rb") as f:
            data = base64.b64encode(f.read()).decode()
        st.markdown(
            f"""
            <style>
            .marca-agua {{ position: fixed; bottom: 20px; right: 20px; width: 80px; opacity: 0.3; z-index: 9999; }}
            </style>
            <img src="data:image/png;base64,{data}" class="marca-agua">
            """, unsafe_allow_html=True
        )


# --- CONFIGURACIÓN DE RUTAS ---
# 1. Hacemos que Streamlit también detecte la ruta dinámicamente (Igual que Webots)
BASE_PATH = os.path.dirname(os.path.abspath(__file__))

FILE_CMD = os.path.join(BASE_PATH, "comandos.json")
FILE_TELEMETRIA = os.path.join(BASE_PATH, "telemetria.json")
FILE_FRAME = os.path.join(BASE_PATH, "last_frame.jpg")

st.set_page_config(page_title="HPE Digital Twin - Predictive NOC", layout="wide")
RUTA_LOGO = os.path.join(BASE_PATH, "logo_principal.png")
# aplicar_marca_agua(RUTA_LOGO) # (Descomenta esto solo si tienes el logo en la misma carpeta)

# --- CONTROL DE NAVEGACIÓN ---
if 'pagina' not in st.session_state: st.session_state.pagina = 'inicio'
if 'unidad_seleccionada' not in st.session_state: st.session_state.unidad_seleccionada = "EN-01"


def leer_telemetria():
    if os.path.exists(FILE_TELEMETRIA):
        for _ in range(3): # Reintenta hasta 3 veces si el archivo está ocupado
            try:
                with open(FILE_TELEMETRIA, "r") as f:
                    return json.load(f)
            except Exception:
                time.sleep(0.05)
    return {"velocidad": 0, "nodo_actual": "Buscando Señal...", "destino": "---", "estado": "Desconectado"}


def enviar_orden(destino, comando="GOTO", apoyo=False):
    try:
        with open(FILE_CMD, "w") as f:
            json.dump({"comando": comando, "destino": destino, "apoyo": apoyo, "t": time.time()}, f)
    except:
        st.error("Error en enlace de control (Uplink)")


# =================================================================
# PÁGINA 1: BIENVENIDA EMPRESARIAL
# =================================================================
if st.session_state.pagina == 'inicio':
    st.markdown("<h1 style='text-align: center; color: #00d4ff;'>🌐 HPE CORPORATE DATA SYSTEMS 🌐</h1>",
                unsafe_allow_html=True)
    st.markdown("<h3 style='text-align: center; color: #a0aec0;'>Predictive Digital Twin & Chaos Engineering NOC</h3>",
                unsafe_allow_html=True)
    st.divider()

    col1, col2, col3 = st.columns([1, 1.5, 1])
    with col2:
        if os.path.exists(RUTA_LOGO):
            with open(RUTA_LOGO, "rb") as f:
                data = base64.b64encode(f.read()).decode()
            st.markdown(
                f'<div style="display: flex; justify-content: center;"><img src="data:image/png;base64,{data}" style="width: 180px; margin-bottom: 10px;"></div>',
                unsafe_allow_html=True)
        else:
            st.markdown(
                '<div style="display: flex; justify-content: center;"><img src="https://cdn-icons-png.flaticon.com/512/2103/2103303.png" style="width: 150px; margin-bottom: 20px;"></div>',
                unsafe_allow_html=True)

        st.write("### Auditoría de Resiliencia en Tiempo Real")
        st.write(
            "Panel de control SRE (*Site Reliability Engineering*) para la monitorización de infraestructura Edge-to-Cloud, evaluación de SLAs y mitigación predictiva de Fallas Grises.")

        if st.button("🚀 INICIALIZAR ENTORNO NOC", use_container_width=True):
            st.session_state.pagina = 'flota'
            st.rerun()

# =================================================================
# PÁGINA 2: INFRAESTRUCTURA EDGE (LISTA DE NODOS)
# =================================================================
elif st.session_state.pagina == 'flota':
    st.header("🖥️ Gestión de Nodos Perimetrales (Edge Cluster)")
    if st.button("⬅️ Cerrar Sesión Segura"):
        st.session_state.pagina = 'inicio'
        st.rerun()

    col_a, col_b = st.columns(2)
    with col_a:
        with st.container(border=True):
            st.subheader("📡 EDGE NODE (Agente Dinámico) EN-01")
            st.caption("Carga útil: Paquete de Misión Crítica | Topología: Anillo Físico")
            if st.button("AUDITAR AGENTE EN-01", use_container_width=True):
                st.session_state.unidad_seleccionada = "EN-01"
                st.session_state.pagina = 'panel'
                st.rerun()
        with st.container(border=True):
            st.subheader("📡 EDGE NODE (Standby) EN-02")
            if st.button("AUDITAR AGENTE EN-02", use_container_width=True):
                st.session_state.unidad_seleccionada = "EN-02"
                st.session_state.pagina = 'panel'
                st.rerun()
    with col_b:
        for i in range(3, 5):
            with st.container(border=True):
                st.subheader(f"📡 EDGE NODE (Standby) EN-0{i}")
                if st.button(f"AUDITAR AGENTE EN-0{i}", key=f"btn_f_{i}", use_container_width=True):
                    st.session_state.unidad_seleccionada = f"EN-0{i}"
                    st.session_state.pagina = 'panel'
                    st.rerun()

# =================================================================
# PÁGINA 3: PANEL OPERATIVO NOC
# =================================================================
elif st.session_state.pagina == 'panel':
    u_id = st.session_state.unidad_seleccionada

    IMAGENES_FIJAS = {
        "EN-02": "https://images.unsplash.com/photo-1558494949-ef010cbdcc31?q=80&w=1000",  # Server rack image
        "EN-03": "https://images.unsplash.com/photo-1606778303063-4601bc7773ea?q=80&w=1000",
        "EN-04": "https://images.unsplash.com/photo-1544197150-b99a580bb7a8?q=80&w=1000"
    }

    if st.button("✖ RETORNAR A VISTA DE CLUSTER", use_container_width=True):
        st.session_state.pagina = 'flota'
        st.rerun()
    st.markdown(f"<h1 style='color: #00d4ff; text-align: center;'>🛡️ TELEMETRÍA DE RED: {u_id}</h1>",
                unsafe_allow_html=True)
    st.divider()

    # --- LECTURA DINÁMICA DE DATOS ---
    if u_id == "EN-01":
        raw_data = leer_telemetria()
        data = {
            "velocidad": raw_data.get("velocidad", 0),
            "nodo_actual": raw_data.get("nodo_actual", "Detectando..."),
            "destino": raw_data.get("destino", "Esperando..."),
            "estado": raw_data.get("estado", "Inactivo"),
            "x": raw_data.get("x", 0.0),
            "z": raw_data.get("z", 0.0),
            "distancia": raw_data.get("distancia", 80.0),
            "latencia": raw_data.get("latencia", 0.0),
            "estado_auditoria": raw_data.get("estado_auditoria", "LIBRE")
        }
    else:
        data = {"velocidad": 0, "nodo_actual": "---", "destino": "---", "estado": "Standby", "x": 0, "z": 0,
                "distancia": 80, "latencia": 0.0, "estado_auditoria": "LIBRE"}

    col_izq, col_cen, col_der = st.columns([1, 1.2, 1])

    # ---------------------------------------------------------
    # COLUMNA 1: TELEMETRÍA Y ALERTAS SLA
    # ---------------------------------------------------------
    with col_izq:
        with st.expander("📊 PIPELINE ETL: DATOS CINEMÁTICOS", expanded=True):
            st.metric("Tasa de Tránsito Física", f"{data['velocidad']} km/h")
            st.write(f"📍 **Gateway Actual:** {data['nodo_actual']}")
            st.write(f"🎯 **Nodo Destino:** {data['destino']}")
            st.write(f"🌍 **Coordenada Topológica:** X: {data['x']:.2f} | Z: {data['z']:.2f}")
            st.write(f"📏 **Distancia a Obstáculo:** {data['distancia']:.2f} m")

        with st.expander("🚨 AUDITOR DE SLA (ACUERDO DE SERVICIO)", expanded=True):
            dist_obj = data['distancia']
            if dist_obj < 5.0:
                st.error("🛑 NETWORK BUFFERING CRÍTICO (Freno físico)")
            elif dist_obj < 15.0:
                st.warning("⚠️ DEGRADACIÓN INMINENTE: Fricción detectada")

            st.info(f"📡 Enlace UDP activo con {u_id}")

        with st.expander("📉 MONITOR DE LATENCIA (Chaos Metrics)", expanded=True):
            latencia_en_vivo = data['latencia']
            if 'latencias_list' not in st.session_state: st.session_state.latencias_list = [0.0] * 30

            st.session_state.latencias_list.append(latencia_en_vivo)
            if len(st.session_state.latencias_list) > 30: st.session_state.latencias_list.pop(0)

            st.area_chart(st.session_state.latencias_list, height=150)

            if latencia_en_vivo < 100:
                status_red = "🟢 SLA NOMINAL"
            elif latencia_en_vivo < 300:
                status_red = "🟡 FALLA GRIS (Throttling)"
            else:
                status_red = "🔴 ESTADO ABSORBENTE (Caída)"

            st.caption(f"📡 Latencia Predictiva: {latencia_en_vivo} ms | Status: {status_red}")

    # ---------------------------------------------------------
    # COLUMNA 2: VIDEO Y LOGS DE AUDITORÍA
    # ---------------------------------------------------------
    with col_cen:
        with st.expander("📷 AUDITORÍA VISUAL ZERO TRUST (YOLOv8)", expanded=True):
            if u_id == "EN-01":
                if os.path.exists(FILE_FRAME):
                    exito = False
                    for intento in range(3):
                        try:
                            with open(FILE_FRAME, "rb") as f:
                                st.image(f.read(), use_container_width=True, caption="Inferencia en el Borde (Edge AI)")
                            exito = True
                            break
                        except PermissionError:
                            time.sleep(0.05)
                    if not exito: st.caption("📷 Sincronizando frame...")
                else:
                    st.warning("Esperando handshake de video UDP...")
            else:
                RUTA_GLB = os.path.join(BASE_PATH, "ZOC_POL2.glb")
                if os.path.exists(RUTA_GLB):
                    visor_3d_glb(RUTA_GLB)
                else:
                    st.image(IMAGENES_FIJAS.get(u_id, ""), use_container_width=True,
                             caption=f"Topología Estática {u_id}")

        with st.expander("🔔 LOGS DE EVENTOS DEL SISTEMA", expanded=True):
            estado_auto = data.get("estado", "IDLE")
            st.success(f"✅ ESTADO DEL PAQUETE: {estado_auto}")

    # ---------------------------------------------------------
    # COLUMNA 3: CONTROLES SRE Y CHAOS ENGINEERING
    # ---------------------------------------------------------
    with col_der:
        with st.expander("🧠 INDICE DE RIESGO ESTRUCTURAL", expanded=True):
            lat_actual = data['latencia']
            if lat_actual >= 900.0:
                modo_operativo = "SPOF COLAPSADO"
                color_estado = "#ff0000"
            elif lat_actual >= 200.0:
                modo_operativo = "DEGRADACIÓN SEVERA"
                color_estado = "#ff4b4b"
            elif 30.0 <= lat_actual <= 50.0:
                modo_operativo = "SLA CUMPLIDO"
                color_estado = "#32cd32"
            else:
                modo_operativo = "FRICCIÓN DE RED"
                color_estado = "#ffa500"

            st.markdown(f"<h2 style='text-align: center; color: {color_estado};'>{modo_operativo}</h2>",
                        unsafe_allow_html=True)

        with st.expander("🗺️ ENRUTAMIENTO DINÁMICO", expanded=True):
            nodos_disponibles = ["N1", "N2", "N3", "N4", "N5", "N6", "N7", "N8", "N9", "N10"]
            dest_sel = st.selectbox("Actualizar tabla de enrutamiento (A*):", nodos_disponibles, key=f"nav_{u_id}")
            if st.button("ENVIAR VECTOR DE RUTA", use_container_width=True):
                enviar_orden(dest_sel, comando="GOTO")
                st.toast(f"Vector A* actualizado: {dest_sel}")

            st.divider()

            # 🔥 LÓGICA ZERO TRUST CORREGIDA
            auditoria_actual = data.get("estado_auditoria", "LIBRE")

            if auditoria_actual == "BLOQUEO_CONFIRMADO" or st.session_state.get('bloqueo_activo'):
                st.session_state.bloqueo_activo = True
                st.error(
                    f"🚨 **ALERTA CIBERNÉTICA:** Nodo {st.session_state.nodo_bloqueado} obstruido. SLA Comprometido.")
                if st.button("✅ RESTAURAR NODO (Mitigación)"):
                    enviar_orden("N1", comando="GOTO")
                    st.session_state.bloqueo_activo = False
                    st.rerun()

            elif auditoria_actual == "FALSO_POSITIVO" and st.session_state.get('bloqueo_activo'):
                st.session_state.bloqueo_activo = False
                st.success("✅ Auditoría Edge completada: FALSO POSITIVO descartado. Vía limpia.")
                st.rerun()

            st.subheader("Inyectar Fallas (Chaos Engineering)")
            nodo_a_bloquear = st.selectbox("Nodo a degradar (SPOF):", nodos_disponibles, key=f"block_{u_id}")

            if st.button("⛔ INYECTAR FALLA (Kill Node)", use_container_width=True, type="secondary"):
                enviar_orden(nodo_a_bloquear, comando="BLOCK_NODE")
                st.session_state.bloqueo_activo = True
                st.session_state.nodo_bloqueado = nodo_a_bloquear
                st.toast(f"Comando de Chaos inyectado en {nodo_a_bloquear}")

        with st.expander("⚙️ PROTOCOLOS SRE AVANZADOS", expanded=True):
            if st.button("⛔ DROP PACKET (Forzar pérdida)", type="primary", use_container_width=True):
                enviar_orden(data['nodo_actual'], comando="STOP")
                st.warning("Paquete destruido. Simulación de Packet Loss.")

            c1, c2 = st.columns(2)
            if c1.button("🔄 FAILOVER", use_container_width=True): st.toast("Ruta alterna pre-calentada.")
            if c2.button("⚖️ LOAD BALANCE", use_container_width=True): st.toast("Tráfico distribuido 50/50.")

            if st.button("⚡ INICIAR REDUNDANCIA DE ENJAMBRE", use_container_width=True):
                import random

                refuerzos = [p for p in ["EN-02", "EN-03", "EN-04"] if p != u_id]
                st.session_state.backup_active = True
                st.session_state.unidad_apoyo = random.choice(refuerzos)
                enviar_orden(data['destino'], apoyo=True)
                st.toast(f"🚨 Sincronización Edge enviada a {st.session_state.unidad_apoyo}")

            if st.session_state.get('backup_active'):
                unidad_aux = st.session_state.get('unidad_apoyo', 'EN-02')
                st.markdown(f"""
                            <div style="background-color: #002b36; padding: 15px; border-radius: 10px; border-left: 5px solid #00d4ff;">
                                <b style="color: #00d4ff;">🤖 STATUS (SWARM):</b> NODOS VINCULADOS<br>
                                <b style="color: #00d4ff;">NODO REDUNDANTE:</b> {unidad_aux}<br>
                                <p style="font-size: 0.85em; color: #85929e; margin-top: 5px;">
                                    Sincronizando telemetría... El nodo {unidad_aux} ha absorbido el 50% de la carga del SLA hacia {data['destino']}.
                                </p>
                            </div>
                        """, unsafe_allow_html=True)

    if u_id == "EN-01":
        time.sleep(0.4)
        st.rerun()