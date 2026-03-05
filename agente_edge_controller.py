from vehicle import Driver
from controller import Keyboard
import numpy as np
import cv2
from ultralytics import YOLO
import csv
import socket
import json
import heapq
import math
import os

# 1. Detecta automáticamente la carpeta exacta donde está guardado este archivo de Python
BASE_PATH = os.path.dirname(os.path.abspath(__file__))

# 2. Crea las rutas basándose en esa carpeta (funcionará en la PC de los jueces, en Mac, Linux, etc.)
FILE_CMD = os.path.join(BASE_PATH, "comandos.json")
FILE_TELEMETRIA = os.path.join(BASE_PATH, "telemetria.json")
FILE_FRAME = os.path.join(BASE_PATH, "last_frame.jpg")

def procesar_comandos_externos():
    """Realiza un escrutinio de los comandos enviados desde la web."""
    if os.path.exists(FILE_CMD):
        try:
            with open(FILE_CMD, "r") as f:
                comando_recibido = json.load(f)

            # ¡CLAVE! Borramos el archivo inmediatamente después de leerlo
            os.remove(FILE_CMD)
            return comando_recibido
        except:
            return None
    return None


# Corrección de Socket (Línea necesaria para el código de tu amigo)
sock_recepcion = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock_recepcion.bind(("127.0.0.1", 5006))  # Puerto para recibir órdenes
sock_recepcion.setblocking(False)

# ==========================================
# 0. CONFIGURACIÓN RED UDP (GEMELO DIGITAL -> C4i)
# ==========================================
UDP_IP = "127.0.0.1"
UDP_PUERTO = 5005
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

# ==========================================
# 1. CEREBRO TOPOLÓGICO (GRAFO UNIDIRECCIONAL)
# ==========================================
coordenadas_nodos = {
    'N1': (39.7736, -56.1644),  # entrada_A
    'N2': (-75.997, -97.7352),  # Entrada_de_A_a_Continuar_A_Linea
    'N3': (-57.5789, 39.7283),  # Salida_A_hacia_EntrarB_ContinuarA
    'N4': (-49.6989, 34.1783),  # Entrar_B
    'N5': (-34.1389, 39.7283),  # salir_de_A_a_Continuar_A
    'N6': (39.7736, -34.0844),  # Salida_De_NodoA_hacia_continuarB_o_hacia_EntradaA
    'N7': (56.0936, -50.5644),  # Continuar_B
    'N8': (99.004, 94.1392),  # Entrada_de_B_a_Continuar_B_lineal
    'N9': (33.9697, -50.385),  # salida_B_hacia_EntradaA_o_ContinuarB
    'N10': (-50.6557, 55.7303)  # Salida_De_B_Hacia_EntrarB_o_ContinuarA
}

dist = lambda n1, n2: math.sqrt((coordenadas_nodos[n1][0] - coordenadas_nodos[n2][0]) ** 2 +
                                (coordenadas_nodos[n1][1] - coordenadas_nodos[n2][1]) ** 2)

mapa_topologico = {
    'N1': {'N2': dist('N1', 'N2')},
    'N2': {'N3': dist('N2', 'N3')},
    'N3': {'N5': dist('N3', 'N5'), 'N4': dist('N3', 'N4')},
    'N5': {'N6': dist('N5', 'N6')},
    'N6': {'N1': dist('N6', 'N1'), 'N7': dist('N6', 'N7')},
    'N7': {'N8': dist('N7', 'N8')},
    'N8': {'N9': dist('N8', 'N9')},
    'N9': {'N5': dist('N9', 'N5'), 'N4': dist('N9', 'N4')},
    'N4': {'N10': dist('N4', 'N10')},
    'N10': {'N7': dist('N10', 'N7'), 'N3': dist('N10', 'N3')}
}


def heuristica(nodo_actual, nodo_objetivo):
    x1, z1 = coordenadas_nodos[nodo_actual]
    x2, z2 = coordenadas_nodos[nodo_objetivo]
    return math.sqrt((x1 - x2) ** 2 + (z1 - z2) ** 2)


def calcular_ruta_a_star(inicio, objetivo):
    frontera = []
    heapq.heappush(frontera, (0, inicio))
    costo_acumulado = {inicio: 0}
    nodos_previos = {inicio: None}

    while frontera:
        _, nodo_actual = heapq.heappop(frontera)
        if nodo_actual == objetivo: break

        for vecino, costo in mapa_topologico[nodo_actual].items():
            nuevo_costo = costo_acumulado[nodo_actual] + costo
            if vecino not in costo_acumulado or nuevo_costo < costo_acumulado[vecino]:
                costo_acumulado[vecino] = nuevo_costo
                prioridad = nuevo_costo + heuristica(vecino, objetivo)
                heapq.heappush(frontera, (prioridad, vecino))
                nodos_previos[vecino] = nodo_actual

    ruta_final = []
    actual = objetivo
    while actual is not None:
        ruta_final.append(actual)
        actual = nodos_previos.get(actual)
    ruta_final.reverse()
    return ruta_final


ruta_actual = calcular_ruta_a_star('N1', 'N9')
indice_ruta = 0

print("\n=================================================")
print(f" [A* DIRIGIDO] Ruta calculada: {ruta_actual}")
print("=================================================\n")

# ==========================================
# 2. INICIALIZACIÓN DEL CHASIS Y SENSORES
# ==========================================
driver = Driver()
timestep = int(driver.getBasicTimeStep())
dt_segundos = timestep / 1000.0

lidar = driver.getDevice("Sick LMS 291")
if lidar: lidar.enable(timestep)
lidar_width = lidar.getHorizontalResolution()

camera = driver.getDevice("camera")
if camera: camera.enable(timestep)

acelerometro = driver.getDevice("accelerometer")
if acelerometro: acelerometro.enable(timestep)

gps = driver.getDevice("gps")
if gps: gps.enable(timestep)

compass = driver.getDevice("compass")
if compass: compass.enable(timestep)

keyboard = Keyboard()
keyboard.enable(timestep)

tiempo_inicio_giro = 0.0
tiempo_ceguera_actual = 1.5

velocidad_crucero = 40.0
driver.setSteeringAngle(0.0)
driver.setBrakeIntensity(0.0)
driver.setCruisingSpeed(velocidad_crucero)
nodos_anillo_interior = ['N4', 'N7', 'N8', 'N9', 'N10']

print("--- Cargando Cerebro IA (ACC + Swarm Protocol)... ---")
modelo = YOLO('yolov8n.pt')

archivo_csv = open('telemetria_avanzada.csv', mode='w', newline='')
escritor_csv = csv.writer(archivo_csv)
escritor_csv.writerow(
    ['Tiempo_s', 'GPS_X', 'GPS_Y', 'Distancia_m', 'Fuerza_G', 'Modo', 'Alerta_YOLO', 'Velocidad_kmh', 'TTC_s',
     'Estado_Red', 'Latencia_Buffer_s'])

ultimo_disparo_foto = 0.0
error_previo = 0.0
velocidad_suavizada = 0.0
estado_maniobra = "CARRIL"
rumbo_objetivo = 0.0
ya_ve_lineas = False
tiempo_frenado_total = 0.0
memoria_yolo = []
tecla_p_presionada_anteriormente = False
alerta_manual = "OFF"
modo_persecucion = False

# --- VARIABLES PARA LA DUALIDAD WEB ---
modo_verificacion_nodo = False
nodo_objetivo_bloqueo = None
tiempo_parada_obstruccion = 0.0
mensaje_mision_web = "Monitoreo SLA Activo"
estado_auditoria_web = "LIBRE"

# VARIABLES HPE (STRESS TEST DE RED)
estado_red = "OPTIMA"
latencia_buffer = 0.0
inicio_caida = 0.0

# VARIABLES ZERO TRUST (CIBERSEGURIDAD)
nodo_bajo_auditoria = None
tiempo_inicio_auditoria = 0.0
falso_positivo_detectado = False

print("--- SISTEMA AUTÓNOMO LISTO Y TRANSMITIENDO A STREAMLIT ---")

# ==========================================
#  BUCLE DE CONTROL PRINCIPAL
# ==========================================
try:
    while driver.step() != -1:
        tiempo_actual = driver.getTime()

        # ==========================================
        #  HPE COMMAND CENTER: RECEPCIÓN DE ÓRDENES NOC
        # ==========================================
        try:
            datos_recibidos, addr = sock_recepcion.recvfrom(1024)
            mensaje_c4 = json.loads(datos_recibidos.decode('utf-8'))

            comando = mensaje_c4.get("comando")
            nodo_afectado = mensaje_c4.get("nodo", "DESCONOCIDO")

            if comando == "KILL_NODE":
                print(f"\n[NOC DOWNLINK] Orden de apagar {nodo_afectado} recibida.")
                print(f"Iniciando auditoría Edge. Validaremos físicamente el {nodo_afectado}...")
                nodo_bajo_auditoria = nodo_afectado
                tiempo_inicio_auditoria = driver.getTime()

            elif comando == "RESTORE_NODE":
                if estado_red == "LINK_DOWN":
                    estado_red = "RESTORED"
                    latencia_buffer = tiempo_actual - inicio_caida
                    print(f"\nNODO {nodo_afectado} EN LÍNEA.")
                    print(f"Latencia mitigada: {latencia_buffer:.2f}s. Reanudando...\n")

        except BlockingIOError:
            pass
        except Exception:
            pass

            # --- ESCUCHA DINÁMICA DEL DASHBOARD ---
        cmd = procesar_comandos_externos()
        if cmd:
            tipo_comando = cmd.get("comando")
            target_nodo = cmd.get("destino")

            if len(ruta_actual) > 0 and indice_ruta < len(ruta_actual):
                nodo_origen = ruta_actual[indice_ruta - 1] if indice_ruta > 0 else ruta_actual[0]
            else:
                nodo_origen = 'N1'

            if tipo_comando == "GOTO":
                print(f" [NUEVA ORDEN] Recalculando vector A* hacia {target_nodo}...")
                ruta_actual = calcular_ruta_a_star(nodo_origen, target_nodo)
                indice_ruta = 1 if len(ruta_actual) > 1 else 0
                modo_verificacion_nodo = False
                estado_auditoria_web = "LIBRE"
                tiempo_parada_obstruccion = 0.0
                mensaje_mision_web = f" Transmitiendo paquete hacia {target_nodo}"

            elif tipo_comando == "BLOCK_NODE":
                print(f"Iniciar Chaos Engineering en {target_nodo}. Desplegando...")
                ruta_actual = calcular_ruta_a_star(nodo_origen, target_nodo)
                indice_ruta = 1 if len(ruta_actual) > 1 else 0
                modo_verificacion_nodo = True
                nodo_objetivo_bloqueo = target_nodo
                estado_auditoria_web = "AUDITANDO"
                tiempo_parada_obstruccion = 0.0
                mensaje_mision_web = f"Auditoría Edge en ruta a SPOF: {target_nodo}"

        key = keyboard.getKey()
        if key == ord('P'):
            if not tecla_p_presionada_anteriormente:
                modo_persecucion = not modo_persecucion
                alerta_manual = "PATROL_ACTIVE" if modo_persecucion else "OFF"
                print(f"MODO PATRULLA: {alerta_manual}")
                tecla_p_presionada_anteriormente = True
        else:
            tecla_p_presionada_anteriormente = False

        velocidad_actual = driver.getCurrentSpeed()
        if math.isnan(velocidad_actual): velocidad_actual = 0.0

        brujula_grados = 0.0
        if compass:
            cv = compass.getValues()
            if not np.isnan(cv[0]) and not np.isnan(cv[1]):
                brujula_grados = (math.atan2(cv[0], cv[1]) * 180.0 / math.pi) % 360.0

        # --- B) NAVEGACIÓN INTELIGENTE ---
        gps_x, gps_z = 0.0, 0.0
        nodo_objetivo_actual = "NINGUNO"
        sector_actual = "DESCONOCIDO"

        if gps:
            gv = gps.getValues()
            if not np.isnan(gv[0]) and not np.isnan(gv[1]):
                gps_x, gps_z = gv[0], gv[1]

                if gps_x >= 0 and gps_z >= 0:
                    sector_actual = "SURESTE"
                elif gps_x < 0 and gps_z >= 0:
                    sector_actual = "SUROESTE"
                elif gps_x >= 0 and gps_z < 0:
                    sector_actual = "NORESTE"
                else:
                    sector_actual = "NOROESTE"

                if indice_ruta < len(ruta_actual):
                    nodo_objetivo_actual = ruta_actual[indice_ruta]
                    obj_x, obj_z = coordenadas_nodos[nodo_objetivo_actual]
                    distancia_al_nodo = math.sqrt((gps_x - obj_x) ** 2 + (gps_z - obj_z) ** 2)

                    if distancia_al_nodo < 7.0 and estado_maniobra in ["CARRIL", "VERIFICANDO_NODO"]:
                        # --- PROTOCOLO DE VERIFICACIÓN (BOTÓN BLOQUEAR) ---
                        if modo_verificacion_nodo and nodo_objetivo_actual == nodo_objetivo_bloqueo:
                            estado_maniobra = "VERIFICANDO_NODO"

                            if tiempo_parada_obstruccion == 0.0:
                                tiempo_parada_obstruccion = driver.getTime()
                                print(
                                    f"\n [AUDITORÍA TÁCTICA] Llegada a {nodo_objetivo_bloqueo}. Iniciando escaneo de 10s...")

                            tiempo_transcurrido = driver.getTime() - tiempo_parada_obstruccion
                            tiempo_restante = max(0, 3 - int(tiempo_transcurrido))

                            if tiempo_transcurrido > 3.0:
                                nodo_donde_estoy_parado = ruta_actual[indice_ruta - 1]
                                destino_recuperacion = 'N9'
                                
                                if 'mejor_distancia' in locals() and mejor_distancia < 15.0:
                                    print(f"Obstrucción confirmada en {nodo_objetivo_bloqueo}.")
                                    mensaje_mision_web = f" Confirmado: {nodo_objetivo_bloqueo} está obstruido."
                                    estado_auditoria_web = "BLOQUEO_CONFIRMADO"
                                    
                                    # Bloqueamos el mapa
                                    for origen in mapa_topologico:
                                        if nodo_objetivo_bloqueo in mapa_topologico[origen]:
                                            mapa_topologico[origen][nodo_objetivo_bloqueo] = float('inf')
                                else:
                                    print(f"[RESULTADO NOC] Falso reporte. Retomando misión hacia {destino_recuperacion}.")
                                    mensaje_mision_web = f"Falso reporte: {nodo_objetivo_bloqueo} libre."
                                    estado_auditoria_web = "FALSO_POSITIVO"
                                
                               
                                print(f"[A* DINÁMICO] Recalculando vector hacia destino final...")
                                ruta_actual = calcular_ruta_a_star(nodo_donde_estoy_parado, destino_recuperacion)
                                indice_ruta = 1
                                    
                                modo_verificacion_nodo = False
                                estado_maniobra = "CARRIL"
                                tiempo_parada_obstruccion = 0.0
                        else:
                            indice_ruta += 1

                        if indice_ruta < len(ruta_actual):
                            siguiente_nodo = ruta_actual[indice_ruta]
                            nx, nz = coordenadas_nodos[siguiente_nodo]

                            rad_hacia_destino = math.atan2(nz - gps_z, nx - gps_x)
                            rumbo_objetivo = (rad_hacia_destino * 180.0 / math.pi) % 360.0
                            distancia_siguiente = math.sqrt((nx - gps_x) ** 2 + (nz - gps_z) ** 2)

                            nodo_alcanzado = ruta_actual[indice_ruta - 1]

                            if nodo_alcanzado == 'N6' and siguiente_nodo == 'N7':
                                estado_maniobra = "GIRO_CIEGAS"
                                tiempo_inicio_giro = driver.getTime()
                                tiempo_ceguera_actual = 3.6
                                rumbo_objetivo = (brujula_grados + 60.0) % 360.0
                            elif nodo_alcanzado == 'N3' and siguiente_nodo == 'N5':
                                estado_maniobra = "GIRO_CIEGAS"
                                tiempo_inicio_giro = driver.getTime()
                                tiempo_ceguera_actual = 1.5
                            elif distancia_siguiente > 40.0:
                                pass
                            else:
                                estado_maniobra = "GIRO_CIEGAS"
                                tiempo_inicio_giro = driver.getTime()
                                tiempo_ceguera_actual = 2.0

                                # --- C) VISIÓN ARTIFICIAL Y SENSORES ---
        angulo_deseado = 0.0
        error = 0.0
        vel_metros_segundo = max(velocidad_actual / 3.6, 0.5)

        valores_g = acelerometro.getValues() if acelerometro else [0.0, 0.0, 0.0]
        fuerza_g_frontal = (valores_g[1] / 9.81) if not math.isnan(valores_g[1]) else 0.0

        # ==========================================
        # 1. ESCÁNER LIDAR
        # ==========================================
        distancia_frontal = 80.0

        rango_imagen = lidar.getRangeImage()
        if rango_imagen is not None:
            apertura = 80
            centro_inicio = max(0, int(lidar_width / 2) - apertura)
            centro_fin = min(lidar_width, int(lidar_width / 2) + apertura)

            rayos_frontales = rango_imagen[centro_inicio:centro_fin]
            if len(rayos_frontales) > 0:
                min_dist = float("inf")
                for r in rayos_frontales:
                    if not np.isinf(r) and not np.isnan(r) and r < min_dist:
                        min_dist = r
                if min_dist != float("inf"):
                    distancia_frontal = min_dist

        distancia_filtrada = distancia_frontal

        # ==========================================
        # 2. VISIÓN ARTIFICIAL
        # ==========================================
        imagen_cruda = camera.getImage()
        cx = -1
        ya_ve_lineas = False
        alerta_automatica = "NONE"
        angulo_linea = 0.0

        if imagen_cruda is not None:
            imagen_np = np.frombuffer(imagen_cruda, np.uint8).reshape((camera.getHeight(), camera.getWidth(), 4))
            imagen_bgr = cv2.cvtColor(imagen_np, cv2.COLOR_BGRA2BGR)
            alto, ancho = imagen_bgr.shape[:2]

            if int(driver.getTime() * 10) % 3 == 0:
                memoria_yolo = []
                resultados = modelo(imagen_bgr, verbose=False)
                for r in resultados:
                    for caja in r.boxes:
                        if float(caja.conf[0]) > 0.15:
                            memoria_yolo.append({
                                'id': int(caja.cls[0]),
                                'conf': float(caja.conf[0]),
                                'box': list(map(int, caja.xyxy[0]))
                            })

            for obj in memoria_yolo:
                x1, y1, x2, y2 = obj['box']
                clase_id = obj['id']
                confianza = obj['conf']

                if clase_id in [2, 5, 7]:
                    altura_obj = y2 - y1
                    centro_x = int((x1 + x2) / 2)
                    centro_y = int((y1 + y2) / 2)

                    cv2.circle(imagen_bgr, (centro_x, centro_y), 15, (0, 255, 0), 1)

                    if altura_obj > (alto * 0.30):
                        cv2.rectangle(imagen_bgr, (x1, y1), (x2, y2), (0, 165, 255), 3)
                        cv2.putText(imagen_bgr, f"OBSTRUCCION: {confianza:.2f}", (x1, y1 - 10),
                                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 165, 255), 2)

                        tiempo_actual = driver.getTime()
                        if (tiempo_actual - ultimo_disparo_foto) > 10.0:
                            try:
                                foto_evidencia = imagen_bgr[
                                    max(0, y1 - 20):min(alto, y2 + 20), max(0, x1 - 20):min(ancho, x2 + 20)]
                                if foto_evidencia.size > 0:
                                    nombre_archivo = f"HPE_Audit_Obstruccion_{int(tiempo_actual)}s.jpg"
                                    cv2.imwrite(nombre_archivo, foto_evidencia)
                                    ultimo_disparo_foto = tiempo_actual
                            except Exception:
                                pass

                elif clase_id == 0:
                    cv2.rectangle(imagen_bgr, (x1, y1), (x2, y2), (0, 0, 255), 2)
                    cv2.putText(imagen_bgr, "CIVIL", (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 2)

                elif clase_id == 9:
                    recorte_semaforo = imagen_bgr[y1:y2, x1:x2]
                    if recorte_semaforo.size > 0:
                        hsv_semaforo = cv2.cvtColor(recorte_semaforo, cv2.COLOR_BGR2HSV)
                        masc_rojo = cv2.inRange(hsv_semaforo, np.array([0, 120, 70]), np.array([10, 255, 255])) + \
                                    cv2.inRange(hsv_semaforo, np.array([170, 120, 70]), np.array([180, 255, 255]))

                        if cv2.countNonZero(masc_rojo) > 15:
                            alerta_automatica = "RED_LIGHT"
                            cv2.rectangle(imagen_bgr, (x1, y1), (x2, y2), (0, 0, 255), 2)
                        else:
                            cv2.rectangle(imagen_bgr, (x1, y1), (x2, y2), (255, 0, 0), 2)

            imagen_ampliada = cv2.resize(imagen_bgr, (800, 600), interpolation=cv2.INTER_LINEAR)
            cv2.imshow("Dashcam IA - C4i", imagen_ampliada)
            cv2.waitKey(1)

            try:
                temp_frame = FILE_FRAME + "_temp.jpg"
                cv2.imwrite(temp_frame, imagen_ampliada)
                os.replace(temp_frame, FILE_FRAME)
            except Exception:
                pass

            puntos_origen = np.float32(
                [[0, alto], [int(ancho * 0.15), int(alto * 0.55)], [int(ancho * 0.85), int(alto * 0.55)],
                 [ancho, alto]])
            puntos_destino = np.float32([[0, alto], [0, 0], [ancho, 0], [ancho, alto]])
            matriz_homografia = cv2.getPerspectiveTransform(puntos_origen, puntos_destino)
            vista_pajaro = cv2.warpPerspective(imagen_bgr, matriz_homografia, (ancho, alto))
            vista_hsv = cv2.cvtColor(vista_pajaro, cv2.COLOR_BGR2HSV)

            mascara_amarilla = cv2.inRange(vista_hsv, np.array([20, 100, 100], dtype=np.uint8),
                                           np.array([40, 255, 255], dtype=np.uint8))
            mascara_blanca = cv2.inRange(vista_hsv, np.array([0, 0, 200], dtype=np.uint8),
                                         np.array([180, 40, 255], dtype=np.uint8))

            momentos_amarillos = cv2.moments(mascara_amarilla)
            if momentos_amarillos["m00"] > 500:
                cx = int(momentos_amarillos["m10"] / momentos_amarillos["m00"])
                ya_ve_lineas = True
            else:
                mascara_blanca[:, int(ancho * 0.5):] = 0
                momentos_blancos = cv2.moments(mascara_blanca)
                if momentos_blancos["m00"] > 500:
                    cx = int(momentos_blancos["m10"] / momentos_blancos["m00"])
                    ya_ve_lineas = True

            target_x = ancho * 0.35

            if indice_ruta < len(ruta_actual):
                nodo_en_curso = ruta_actual[indice_ruta]
                if nodo_en_curso in nodos_anillo_interior:
                    target_x = ancho * 0.20
            else:
                target_x = ancho * 0.35
                mensaje_mision_web = "🏁 Destino alcanzado. Vehículo en posición."

            if cx != -1:
                error = cx - target_x
                derivada = error - error_previo
                angulo_linea = np.clip((error * 0.015) + (derivada * 0.05), -0.6, 0.6)
                error_previo = error
            else:
                error = error_previo
                angulo_linea = np.clip((error * 0.015), -0.6, 0.6)

        # --- D) MÁQUINA DE ESTADOS ACTUADORA ---
        if estado_maniobra == "GIRO_CIEGAS":
            modo_actual_log = "KINEMATIC_TURN"
            driver.setBrakeIntensity(0.0)
            L = 2.9

            diferencia_grados = rumbo_objetivo - brujula_grados
            if diferencia_grados > 180:
                diferencia_grados -= 360
            elif diferencia_grados < -180:
                diferencia_grados += 360
            error_theta_rad = math.radians(diferencia_grados)

            velocidad_objetivo_kmh = np.interp(abs(diferencia_grados), [0, 60], [18.0, 8.0])
            velocidad_suavizada = (0.8 * velocidad_suavizada) + (0.2 * velocidad_objetivo_kmh)
            driver.setCruisingSpeed(velocidad_suavizada)

            tiempo_prediccion = 1.8 if abs(diferencia_grados) > 45.0 else 0.8
            theta_dot_req = error_theta_rad / tiempo_prediccion
            delta_rad = math.atan((theta_dot_req * L) / vel_metros_segundo)

            angulo_deseado = -np.clip(delta_rad, -0.6, 0.6)
            umbral_salida = 3.0 if abs(diferencia_grados) < 45.0 else 6.0

            if driver.getTime() - tiempo_inicio_giro > tiempo_ceguera_actual:
                if abs(diferencia_grados) < umbral_salida or (
                        ya_ve_lineas and cx < (ancho * 0.4) and abs(diferencia_grados) < 15.0):
                    estado_maniobra = "CARRIL"

        elif estado_maniobra == "VERIFICANDO_NODO":
            driver.setCruisingSpeed(0.0)
            driver.setBrakeIntensity(1.0)
            angulo_deseado = 0.0
            modo_actual_log = "AUDIT_STOP"

        else:
            velocidad_objetivo = np.interp(abs(error), [0, 45], [40.0, 15.0])
            velocidad_suavizada = (0.8 * velocidad_suavizada) + (0.2 * velocidad_objetivo)

            if (velocidad_actual / 3.6) > ((velocidad_objetivo / 3.6) + 1.0):
                driver.setBrakeIntensity(0.6)
            else:
                driver.setBrakeIntensity(0.0)

            driver.setCruisingSpeed(velocidad_suavizada)
            angulo_deseado = angulo_linea
            modo_actual_log = "PATROL"

        # ==========================================
        #  SISTEMA AEB
        # ==========================================
        aeb_activo = False
        mejor_distancia = 80.0
        fuente_distancia = "NINGUNA"

        if rango_imagen is not None:
            apertura = 100
            centro_inicio = max(0, int(lidar_width / 2) - apertura)
            centro_fin = min(lidar_width, int(lidar_width / 2) + apertura)
            rayos = rango_imagen[centro_inicio:centro_fin]
            angulo_total = lidar.getFov()

            for i, r in enumerate(rayos):
                if not np.isinf(r) and not np.isnan(r) and r > 1.2:
                    indice_global = centro_inicio + i
                    angulo_rayo = ((indice_global / lidar_width) * angulo_total) - (angulo_total / 2)

                    x_rayo = r * math.cos(angulo_rayo)
                    y_rayo = r * math.sin(angulo_rayo)
                    tolerancia_lateral = 1.6

                    if abs(y_rayo) < tolerancia_lateral and x_rayo > 1.2:
                        if x_rayo < mejor_distancia:
                            mejor_distancia = x_rayo
                            fuente_distancia = "LIDAR_CARRIL"

        if camera:
            fov_horizontal = camera.getFov()
            ancho_img = camera.getWidth()
            focal_pix = (ancho_img / 2) / math.tan(fov_horizontal / 2)

            for obj in memoria_yolo:
                if obj['id'] in [0, 2, 5, 7]:
                    x1, y1, x2, y2 = obj['box']
                    centro_x = (x1 + x2) // 2
                    if ((ancho_img / 2) - (ancho_img * 0.35)) < centro_x < ((ancho_img / 2) + (ancho_img * 0.35)):
                        altura_pix = y2 - y1
                        if altura_pix > 0:
                            distancia_est = (1.8 * focal_pix) / altura_pix
                            if distancia_est < mejor_distancia:
                                mejor_distancia = distancia_est
                                fuente_distancia = "YOLO_VISION"

        vel_ms = max(velocidad_actual / 3.6, 0.1)
        

        distancia_frenado_critica = (vel_ms ** 2) / (2 * 3.5)

        zona_full = distancia_frenado_critica + 4.0   # Agregamos 4 metros secos de colchón
        zona_strong = distancia_frenado_critica * 2.0 # Frena al doble de distancia
        zona_alerta = distancia_frenado_critica * 3.5 
        TTC = mejor_distancia / vel_ms

        if mejor_distancia < 80.0:
            if mejor_distancia <= zona_full:
                driver.setBrakeIntensity(1.0)
                driver.setCruisingSpeed(0.0)
                modo_actual_log = "AEB_FULL"
                aeb_activo = True
            elif mejor_distancia <= zona_strong:
                driver.setBrakeIntensity(0.8) # Frenado fuerte inmediato
                driver.setCruisingSpeed(velocidad_actual * 0.3)
                modo_actual_log = "AEB_STRONG"
                aeb_activo = True
            elif mejor_distancia <= zona_alerta:
                if modo_actual_log not in ["AEB_FULL", "AEB_STRONG", "KINEMATIC_TURN"]:
                    driver.setBrakeIntensity(0.4) # Toque suave a los frenos
                    driver.setCruisingSpeed(velocidad_actual * 0.6)
                    modo_actual_log = "AEB_SOFT"
                aeb_activo = True

        if estado_red == "LINK_DOWN":
            driver.setCruisingSpeed(0.0)
            driver.setBrakeIntensity(1.0)
            angulo_deseado = 0.0
            modo_actual_log = "NETWORK_BUFFERING"

        if indice_ruta >= len(ruta_actual):
            #Frenado ABS progresivo para evitar derrapes infinitos
            driver.setCruisingSpeed(0.0)
            if velocidad_actual > 10.0:
                driver.setBrakeIntensity(0.4) # Frena moderadamente si va rápido
            else:
                driver.setBrakeIntensity(1.0) # Clava el freno cuando está casi detenido
            
            # Dejamos que OpenCV controle el volante mientras se detiene. NO forzamos a 0.0
            angulo_deseado = angulo_linea 
            modo_actual_log = "STANDBY"

        driver.setSteeringAngle(angulo_deseado)

        paquete_nube = {
            "unidad_id": "EN-01",
            "timestamp": round(tiempo_actual, 2),
            "coordenadas": {"x": round(gps_x, 2), "z": round(gps_z, 2)},
            "sector": sector_actual,
            "estado": modo_actual_log,
            "velocidad_kmh": round(velocidad_actual, 1),
            "fuerza_g": round(fuerza_g_frontal, 2),
            "alerta_automatica": alerta_automatica,
            "alerta_manual": alerta_manual,
            "estado_red": estado_red
        }
        try:
            sock.sendto(json.dumps(paquete_nube).encode('utf-8'), (UDP_IP, UDP_PUERTO))
        except Exception:
            pass

        if gps:
            coordenadas = gps.getValues()
            gps_x = coordenadas[0]
            gps_y = coordenadas[1]
        else:
            gps_x, gps_y = 0.0, 0.0

        if modo_actual_log == "AEB_FULL":
            if tiempo_frenado_total == 0.0:
                tiempo_frenado_total = tiempo_actual
            elif (tiempo_actual - tiempo_frenado_total) > 4.0:
                alerta_automatica = f"BLOQUEO_RUTA_{nodo_objetivo_actual}"
        else:
            tiempo_frenado_total = 0.0

        if nodo_bajo_auditoria is not None and nodo_bajo_auditoria in coordenadas_nodos:
            nx, nz = coordenadas_nodos[nodo_bajo_auditoria]
            dist_auditoria = math.sqrt((gps_x - nx) ** 2 + (gps_z - nz) ** 2)

            if dist_auditoria < 15.0:
                if modo_actual_log == "AEB_FULL" or (velocidad_actual < 1.0 and aeb_activo):
                    estado_red = "LINK_DOWN"
                    inicio_caida = driver.getTime()
                    nodo_bajo_auditoria = None
                elif dist_auditoria < 7.0 and velocidad_actual > 10.0:
                    falso_positivo_detectado = True
                    nodo_bajo_auditoria = None

        escritor_csv.writerow([
            round(tiempo_actual, 2),
            round(gps_x, 2),
            round(gps_y, 2),
            round(mejor_distancia, 2),
            round(fuerza_g_frontal, 2),
            modo_actual_log,
            alerta_automatica,
            round(velocidad_actual, 2),
            round(TTC, 2),
            estado_red,
            round(latencia_buffer, 2)
        ])

        latencia_calculada = velocidad_actual * 1.0

        if modo_actual_log in ["AEB_FULL", "AEB_STRONG"]:
            latencia_calculada = 350.0
        elif estado_red == "LINK_DOWN":
            latencia_calculada = 999.0

        telemetria_web = {
            "velocidad": round(velocidad_actual, 1),
            "nodo_actual": sector_actual,
            "destino": nodo_objetivo_actual,
            "estado": mensaje_mision_web,
            "estado_auditoria": estado_auditoria_web,
            "x": round(gps_x, 2),
            "z": round(gps_z, 2),
            "distancia": round(mejor_distancia, 2),
            "latencia": round(latencia_calculada, 1)
        }


        temp_file = FILE_TELEMETRIA + ".tmp"
        try:
            with open(temp_file, "w") as f:
                json.dump(telemetria_web, f)
            os.replace(temp_file, FILE_TELEMETRIA) # Sobreescribe de golpe
        except Exception as e:
            # Si Streamlit lo estaba leyendo justo en ese milisegundo, lo ignoramos y lo intentamos en el siguiente frame
            pass

finally:
    # ESTE BLOQUE SE ASEGURA DE CERRAR EL CSV AUNQUE CRASHEE O LO DETENGAS
    print("\nCerrando y guardando Dataset de Telemetría...")
    archivo_csv.flush()
    archivo_csv.close()
    sock.close()