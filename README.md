# 🏎️ HPE CDS Tech Challenge: Gemelo Digital & Chaos Engineering en el Edge

![Status](https://img.shields.io/badge/Status-Release_Candidate-success)
![Python](https://img.shields.io/badge/Python-3.9%2B-blue)
![AI](https://img.shields.io/badge/Edge_AI-YOLOv8-orange)
![Simulation](https://img.shields.io/badge/Simulator-Webots-lightgrey)

> **Equipo:** "Los Foráneos" (Benemérita Universidad Autónoma de Puebla - BUAP)
> **Proyecto para la fase clasificatoria del HPE CDS Tech Challenge 2026**

---

## 📖 Visión General
Este proyecto presenta una arquitectura de resiliencia predictiva basada en un **Gemelo Digital Edge-to-Cloud**. Diseñado para infraestructuras corporativas de misión crítica, el sistema abandona el monitoreo reactivo tradicional en favor de un modelo proactivo impulsado por **Chaos Engineering** y **Zero Trust**.

A través del simulador **Cyberbotics Webots**, modelamos un "Agente Edge" (un vehículo de servicios de emergencia) que actúa como la manifestación física y cinemática de un paquete de datos enrutado a través de una red corporativa.

### 🎥 Demostración en Video
![passingPeopleGIF](https://github.com/user-attachments/assets/d6d04395-c2b5-4875-a54d-fed87e1c9c8a)
---

## 🏗️ Arquitectura del Sistema

Nuestra arquitectura se divide en dos planos principales, comunicados mediante un Pipeline ETL bidireccional asíncrono sobre UDP:

1. **Plano de Datos (On-Premise / Edge):**
   * Vehículo autónomo en **Webots** operando localmente.
   * Navegación heurística mediante algoritmo **A***.
   * Control cinemático de trayectoria vía **OpenCV**.
   * Auditoría de entorno in situ usando **LiDAR** y **YOLOv8** (Deep Packet Inspection).

2. **Plano de Control (NOC / Cloud):**
   * Dashboard SRE (Site Reliability Engineering) construido con **Streamlit**.
   * Inyección dinámica de perturbaciones físicas (*Chaos Engineering*).
   * Monitoreo de latencia en tiempo real y mapeo predictivo de riesgos mediante Estimación de Densidad de Kernel (**KDE**).

---

## ✨ Características Principales (Features)

* **🛡️ Zero Trust & Auditoría Local:** El agente no confía ciegamente en las órdenes de apagado del NOC. Utiliza su propia cámara y el modelo YOLOv8 para auditar físicamente la coordenada y descartar falsos positivos.
* **🌪️ Chaos Engineering Dinámico:** Inyección de bloqueos topológicos (SPOF) en tiempo real desde la web para medir el *Costo de Indisponibilidad* y la degradación del SLA.
* **📊 Métrica Directa de Red:** El sistema traduce demoras físicas reales (ej. tiempo de *buffering* al frenar por un obstáculo) a métricas de telecomunicaciones.
* **🛑 Autonomous Emergency Braking (AEB):** Frenado de emergencia como mecanismo de control de congestión física basado en cinemática.

---

## 🛠️ Tecnologías Utilizadas

* **Simulación:** Cyberbotics Webots
* **Computer Vision & IA:** Ultralytics YOLOv8, OpenCV
* **Backend & Telemetría:** Python, Sockets (UDP), JSON
* **Frontend NOC:** Streamlit, Pandas, Matplotlib / Seaborn
* **Matemáticas y Enrutamiento:** Algoritmo A*, Ecuaciones Cinemáticas, KDE

---

## 🚀 Instalación y Despliegue

### Requisitos Previos
* [Webots](https://cyberbotics.com/) (Versión R2023b o superior).
* Python 3.9+.
* Instalar dependencias:
```bash
pip install ultralytics opencv-python numpy streamlit pandas matplotlib seaborn
```

### Instrucciones de Ejecución

**Paso 1: Iniciar el Centro de Operaciones (NOC)**
Abre una terminal en la raíz del proyecto y ejecuta el dashboard:
```bash
python -m streamlit run noc_dashboard.py
```

**Paso 2: Iniciar el Gemelo Digital**
1. Abre Webots y carga el archivo del mundo (`.wbt`).
2. Asegúrate de que el controlador del vehículo apunte al script `agente_edge.py`.
3. Presiona el botón de **Play** en Webots.

**Paso 3: Inyección de Caos (Validación PoC)**
Para esta fase de Prueba de Concepto, la inyección de fallas se realiza directamente en la capa física. Mueve o coloca los obstáculos dinámicos (cajas o vehículos) directamente en el entorno 3D de Webots. Observa cómo el Agente Edge audita la zona con su cámara, ejecuta el frenado autónomo y cómo el dashboard en Streamlit traduce esa retención física en degradación del SLA en tiempo real.

---
## 🧪 Reproducibilidad

Los experimentos presentados en el documento técnico pueden reproducirse utilizando los conjuntos de datos incluidos en el directorio analytics/.

Los archivos CSV de telemetría corresponden a distintos escenarios experimentales del sistema:

- *Ruta Óptima:* ejecución sin perturbaciones ni congestión.
- *Perturbación Leve:* presencia de obstrucciones temporales que generan micro-retenciones en el agente.
- *Throttling Crónico:* acumulación progresiva de congestión que produce degradación significativa del SLA.
- *Fallo Total (SPOF):* bloqueo permanente de un nodo crítico que impide alcanzar el destino.

Estos registros permiten analizar el comportamiento del sistema, reproducir las gráficas de latencia y generar los mapas de riesgo mediante los scripts contenidos en el mismo directorio.

Los scripts de análisis (Graficas de telemetria.py y Mapa2.0.py) permiten reconstruir las visualizaciones utilizadas en el documento técnico.

## 📂 Estructura del Repositorio
```text
📦 HPE-CDS-Los-Foraneos
 ┣ 📂 analytics                # Scripts y datasets de experimentación (ETL / KDE)
 ┃ ┣ 📜 Graficas de telemetria.py
 ┃ ┣ 📜 Mapa2.0.py
 ┃ ┣ 📜 telemetria_Optima.csv
 ┃ ┣ 📜 telemetria_Saturacion.csv
 ┃ ┣ 📜 telemetria_FalloTotal.csv
 ┃ ┣ 📜 telemetria_falloN3.csv
 ┃ ┗ 📜 telemetria_avanzadaMapaV.csv
 ┣ 📂 controllers
 ┃ ┗ 📂 agente_edge_controller
 ┃   ┗ 📜 agente_edge_controller.py    # Script principal de Webots (IA, YOLO, A*)
 ┣ 📂 dashboard
 ┃ ┗ 📜 noc_dashboard.py               # Interfaz web SRE en Streamlit
 ┣ 📂 worlds
 ┃ ┗ 📜 ciudad_anillo.wbt              # Entorno virtual de simulación 3D
 ┣ 📜 Gemelo_Digital_Doc_tecnico.pdf          # Documento técnico IEEE
 ┗ 📜 README.md                        # Este archivo
```

---

## 👥 El Equipo "Los Foráneos"

* **Alondra M. Pérez Ramírez** - *Data & Network Architecture*
* **Roberto Moreno Mendoza** - *Edge Computing & Computer Vision*
* **Joel Pablo Vargas** - *Simulation & Kinematics*

Agradecimiento especial a nuestro asesor titular, **Dr. Fabricio Otoniel Pérez Pérez**, por su inestimable apoyo en este proyecto.

