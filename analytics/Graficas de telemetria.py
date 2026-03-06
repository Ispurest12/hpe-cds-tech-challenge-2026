import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

# Configuración visual
sns.set_theme(style="whitegrid")
plt.figure(figsize=(12, 6))

# Diccionario con tus 4 archivos y cómo queremos que se vean en la gráfica
archivos = {
    'telemetria_Optima.csv': {'nombre': '1. Baseline (Red Óptima)', 'color': '#2ecc71', 'estilo': '-'},
    'telemetria_falloN3.csv': {'nombre': '2. Latencia Temporal (Downtime 10s)', 'color': '#f1c40f', 'estilo': '--'},
    'telemetria_Saturacion.csv': {'nombre': '3. Red Saturada (Throttling)', 'color': '#e67e22', 'estilo': '-.'},
    'telemetria_FalloTotal.csv': {'nombre': '4. Falla Catastrófica (SPOF / Timeout)', 'color': '#e74c3c', 'estilo': ':'}
}

for archivo, config in archivos.items():
    try:
        df = pd.read_csv(archivo)
        # Suavizamos un poco la línea de velocidad para que se vea más elegante
        df['Velocidad_Suavizada'] = df['Velocidad_kmh'].rolling(window=5, min_periods=1).mean()

        plt.plot(df['Tiempo_s'], df['Velocidad_Suavizada'],
                 label=config['nombre'], color=config['color'],
                 linestyle=config['estilo'], linewidth=2.5)
    except FileNotFoundError:
        print(f"Archivo {archivo} no encontrado.")

# Detalles estéticos de la gráfica
plt.title('HPE Digital Twin: Análisis de Impacto en SLA (Degradación de Red)', fontsize=16, fontweight='bold')
plt.xlabel('Tiempo de Simulación (Segundos)', fontsize=12)
plt.ylabel('Velocidad de Transmisión del Paquete (km/h)', fontsize=12)

# Añadimos áreas de contexto
plt.axhspan(0, 5, color='red', alpha=0.1, label='Zona Crítica (Buffering / Packet Drop)')

plt.legend(loc='upper right', shadow=True)
plt.tight_layout()


plt.savefig('Degradacion.png', dpi=300)
plt.show()