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
*[¡AQUÍ! Coloca el link de YouTube o inserta un GIF de tu coche frenando frente a la caja]*
[![Video Demo](https://img.shields.io/badge/Watch-Video_Demo-red)](#)

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
