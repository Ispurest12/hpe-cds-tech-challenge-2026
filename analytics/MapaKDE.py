
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap

# 1. CARGA DE TELEMETRÍA LIMPIA
df = pd.read_csv('telemetria_avanzadaMapaV.csv')

#Quitamos espacios invisibles de los nombres de las columnas
df.columns = df.columns.str.strip()

# Imprimimos las columnas para confirmar que ya están limpias
print("Columnas detectadas y limpias:", df.columns.tolist())

# 2. FILTRO DE EVENTOS
# (Si tu CSV no tiene Estado_Red, ignoramos esa parte para que no crashee)
if 'Estado_Red' in df.columns:
    df_emergencias = df[
        (df['Estado_Red'] == 'LINK_DOWN') |
        (df['Modo'].isin(['AEB_FULL', 'NETWORK_BUFFERING']))
    ].copy()
else:
    print("'Estado_Red' no detectado. Filtrando por obstrucciones físicas (AEB_FULL).")
    df_emergencias = df[df['Modo'].isin(['AEB_FULL', 'NETWORK_BUFFERING'])].copy()

# Verificamos que sí hayamos atrapado eventos de emergencia
if df_emergencias.empty:
    print("ADVERTENCIA: No se encontró ningún freno de emergencia en el CSV. Revisa si el coche realmente frenó con 'AEB_FULL'.")
# 2. DEFINICIÓN DEL COSTO ESTRUCTURAL (C_i)
def calcular_costo_estructural(x, y):
    # N1 y N5: CORE ROUTERS (SPOF Crítico) -> C_i Alto
    if (abs(x - 39.77) < 15 and abs(y - (-56.16)) < 15) or \
            (abs(x - (-34.13)) < 15 and abs(y - 39.72) < 15):
        return 15.0

        # N3 y N7: ENLACES SECUNDARIOS -> C_i Medio
    elif (abs(x - (-57.5)) < 15 and abs(y - 39.7) < 15) or \
            (abs(x - 56.0) < 15 and abs(y - (-50.5)) < 15):
        return 5.0

        # PERIFÉRICOS -> C_i Base
    else:
        return 1.0

    # Aplicamos C_i al dataset


df_emergencias['C_i'] = df_emergencias.apply(
    lambda row: calcular_costo_estructural(row['GPS_X'], row['GPS_Y']), axis=1
)

# 3. PALETA SEMÁFORO HPE
colores = ["#ffffff00", "#2ecc71", "#f1c40f", "#e74c3c"]
cmap_semaforo = LinearSegmentedColormap.from_list("semaforo_hpe", colores)

# 4. RENDERIZADO DEL MAPA ESTADÍSTICO
sns.set_theme(style="whitegrid")
fig, ax = plt.subplots(figsize=(12, 8))

# Topología Base
ax.scatter(df['GPS_X'], df['GPS_Y'], color='#bdc3c7', s=3, alpha=0.5, label="Topología de Red")

# E[C_i] = KDE * C_i (El mapa grafica la Esperanza Matemática)
kde = sns.kdeplot(
    x=df_emergencias['GPS_X'],
    y=df_emergencias['GPS_Y'],
    weights=df_emergencias['C_i'],
    cmap=cmap_semaforo,
    fill=True,
    thresh=0.01,
    alpha=0.85,
    bw_adjust=0.3,
    cbar=True,
    cbar_kws={'label': 'Índice de Riesgo Normalizado (IR_i)'},
    ax=ax
)


# Seaborn siempre guarda la barra de colores en el último "eje" de la figura
cbar_ax = fig.axes[-1]
cbar_ax.yaxis.label.set_size(12)
cbar_ax.yaxis.label.set_weight('bold')

# Convertimos los números feos en etiquetas corporativas
ticks = cbar_ax.get_yticks()
if len(ticks) >= 2:
    cbar_ax.set_yticks([ticks[0], ticks[len(ticks)//2], ticks[-1]])
    cbar_ax.set_yticklabels(['0.0 (Bajo)', '0.5 (Moderado)', '1.0 (Crítico)'])

plt.title("HPE CDS: Distribución Espacial del Costo Esperado de Falla (E[C_i])", fontsize=15, fontweight='bold')
plt.xlabel("Coordenada Longitudinal X (GPS)", fontsize=12)
plt.ylabel("Coordenada Latitudinal Y (GPS)", fontsize=12)
plt.legend(loc='upper right')

# Agregamos una marca de agua estilo consultoría
plt.text(0.99, 0.01, 'Modelo Analítico: E[C_i] = P(F_i) * C_i',
         horizontalalignment='right', verticalalignment='bottom',
         transform=ax.transAxes, fontsize=10, color='gray')
plt.scatter(df_emergencias['GPS_X'], df_emergencias['GPS_Y'], color='black', s=15, alpha=0.7, marker='x', label="Evidencia Empírica (Bloqueo)")
plt.savefig("Mapa_Calor_HPE_Final.png", dpi=300, bbox_inches='tight')
plt.show()