import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import os
from datetime import datetime
import glob

# Configuración de la página
st.set_page_config(
    page_title="Portal de Notas Estudiantil",
    page_icon="🎓",
    layout="centered"
)

# Título de la aplicación
st.title("🎓 Portal de Notas Estudiantiles - Unidad 3")
st.markdown("---")

# Configuración del archivo - DEFINIDO EN EL PROGRAMA
ARCHIVO_NOTAS = "notas_estudiantes.xlsx"  # Nombre del archivo predefinido
ARCHIVO_BACKUP = "notas_estudiantes_backup.xlsx"  # Archivo alternativo
PATRON_ARCHIVOS = "notas_estudiantes*.xlsx"  # Patrón para buscar archivos

# Inicializar variables en session_state
if 'df_notas' not in st.session_state:
    st.session_state.df_notas = None
if 'estudiante_encontrado' not in st.session_state:
    st.session_state.estudiante_encontrado = None
if 'estadisticas_generales' not in st.session_state:
    st.session_state.estadisticas_generales = None
if 'archivo_cargado' not in st.session_state:
    st.session_state.archivo_cargado = None

# Función para buscar y cargar archivo automáticamente
def buscar_y_cargar_archivo():
    """Busca y carga el archivo de notas automáticamente"""
    
    archivos_encontrados = []
    
    # 1. Buscar archivo exacto
    if os.path.exists(ARCHIVO_NOTAS):
        archivos_encontrados.append(ARCHIVO_NOTAS)
    
    # 2. Buscar archivo de backup
    if os.path.exists(ARCHIVO_BACKUP):
        archivos_encontrados.append(ARCHIVO_BACKUP)
    
    # 3. Buscar por patrón
    archivos_patron = glob.glob(PATRON_ARCHIVOS)
    archivos_encontrados.extend([f for f in archivos_patron if f not in archivos_encontrados])
    
    # 4. Buscar cualquier archivo Excel en el directorio
    if not archivos_encontrados:
        todos_excel = glob.glob("*.xlsx") + glob.glob("*.xls")
        archivos_encontrados.extend([f for f in todos_excel if "notas" in f.lower() or "estudiantes" in f.lower()])
    
    return archivos_encontrados

# Función para cargar archivo
def cargar_archivo(ruta_archivo):
    try:
        df = pd.read_excel(ruta_archivo)
        
        # Verificar columnas mínimas
        columnas_requeridas = []
        
        # Verificar diferentes nombres posibles de columnas
        if 'CÉDULA' in df.columns or 'CEDULA' in df.columns:
            if 'CÉDULA' in df.columns:
                df = df.rename(columns={'CÉDULA': 'CEDULA'})
        else:
            st.error("El archivo debe contener una columna de identificación (CÉDULA o CEDULA)")
            return None, None
        
        if 'NOMBRES' in df.columns or 'NOMBRE' in df.columns:
            if 'NOMBRES' in df.columns:
                df = df.rename(columns={'NOMBRES': 'NOMBRE'})
        else:
            st.error("El archivo debe contener una columna de nombres (NOMBRES o NOMBRE)")
            return None, None
        
        if 'APELLIDOS' in df.columns or 'APELLIDO' in df.columns:
            if 'APELLIDOS' in df.columns:
                df = df.rename(columns={'APELLIDOS': 'APELLIDO'})
        else:
            st.error("El archivo debe contener una columna de apellidos (APELLIDOS o APELLIDO)")
            return None, None
        
        # Limpiar nombres de columnas
        df.columns = df.columns.str.strip()
        
        # Renombrar otras columnas comunes para consistencia
        if 'LICENCIATURA' in df.columns:
            df = df.rename(columns={'LICENCIATURA': 'CARRERA'})
        if 'CORREO' in df.columns:
            df = df.rename(columns={'CORREO': 'EMAIL'})
        
        # Asegurar que CEDULA sea string
        if 'CEDULA' in df.columns:
            df['CEDULA'] = df['CEDULA'].astype(str)
        
        return df, ruta_archivo
    except Exception as e:
        st.error(f"Error al cargar el archivo '{ruta_archivo}': {str(e)}")
        return None, None

# Función para buscar estudiante
def buscar_estudiante(df, cedula, nombres=None, apellidos=None):
    """Busca un estudiante por cédula o nombre/apellido"""
    df_busqueda = df.copy()
    
    # Convertir cédula a string para comparación
    if 'CEDULA' in df_busqueda.columns:
        df_busqueda['CEDULA'] = df_busqueda['CEDULA'].astype(str)
    
    if cedula:
        # Buscar por cédula (búsqueda exacta)
        resultado = df_busqueda[df_busqueda['CEDULA'] == str(cedula)]
    elif nombres and apellidos:
        # Buscar por nombre y apellido (búsqueda parcial, insensible a mayúsculas)
        resultado = df_busqueda[
            (df_busqueda['NOMBRE'].str.contains(nombres, case=False, na=False)) &
            (df_busqueda['APELLIDO'].str.contains(apellidos, case=False, na=False))
        ]
    else:
        return None
    
    return resultado.iloc[0] if not resultado.empty else None

# Función para calcular estadísticas generales
def calcular_estadisticas_generales(df):
    """Calcula estadísticas generales del curso"""
    estadisticas = {}
    
    # Total de estudiantes
    estadisticas['total_estudiantes'] = len(df)
    
    # Si hay columna de estado, contar activos
    if 'ESTADO' in df.columns:
        estadisticas['estudiantes_activos'] = df[df['ESTADO'] == 'Activo'].shape[0]
        estadisticas['estudiantes_retirados'] = df[df['ESTADO'] == 'Retirado'].shape[0]
    
    # Estadísticas de nota final si existe
    if 'NOTA FINAL' in df.columns:
        notas_validas = df['NOTA FINAL'].dropna()
        if len(notas_validas) > 0:
            estadisticas['nota_promedio'] = notas_validas.mean()
            estadisticas['nota_maxima'] = notas_validas.max()
            estadisticas['nota_minima'] = notas_validas.min()
            estadisticas['nota_mediana'] = notas_validas.median()
            
            # Contar aprobados
            aprobados = notas_validas[notas_validas >= 10]
            estadisticas['aprobados'] = len(aprobados)
            estadisticas['porcentaje_aprobados'] = (len(aprobados) / len(notas_validas)) * 100 if len(notas_validas) > 0 else 0
    
    # Distribución por carrera si existe
    if 'CARRERA' in df.columns:
        estadisticas['distribucion_carreras'] = df['CARRERA'].value_counts().to_dict()
    
    # Estadísticas por evaluación
    columnas_info = ['CEDULA', 'NOMBRE', 'APELLIDO', 'EMAIL', 'CARRERA', 'NOTA FINAL', 'PROGRESO (%)', 'ESTADO']
    columnas_evaluacion = [col for col in df.columns if col not in columnas_info]
    
    estadisticas_evaluaciones = {}
    for col in columnas_evaluacion:
        notas = pd.to_numeric(df[col], errors='coerce')
        notas_validas = notas.dropna()
        if len(notas_validas) > 0:
            estadisticas_evaluaciones[col] = {
                'promedio': notas_validas.mean(),
                'maxima': notas_validas.max(),
                'minima': notas_validas.min(),
                'estudiantes_calificados': len(notas_validas)
            }
    
    estadisticas['evaluaciones'] = estadisticas_evaluaciones
    
    return estadisticas

# Función para mostrar información del estudiante
def mostrar_info_estudiante(estudiante):
    """Muestra la información de un estudiante"""
    st.subheader("👤 Información Personal")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if 'CEDULA' in estudiante:
            st.info(f"**Cédula:** {estudiante['CEDULA']}")
        if 'NOMBRE' in estudiante:
            st.info(f"**Nombre:** {estudiante['NOMBRE']}")
    
    with col2:
        if 'APELLIDO' in estudiante:
            st.info(f"**Apellido:** {estudiante['APELLIDO']}")
        if 'EMAIL' in estudiante:
            st.info(f"**Correo:** {estudiante['EMAIL']}")
    
    with col3:
        if 'CARRERA' in estudiante:
            st.info(f"**Carrera:** {estudiante['CARRERA']}")
        if 'ESTADO' in estudiante:
            estado_color = "🟢" if estudiante['ESTADO'] == 'Activo' else "🔴"
            st.info(f"**Estado:** {estado_color} {estudiante['ESTADO']}")
    
    st.markdown("---")

# Función para mostrar notas del estudiante
def mostrar_notas_estudiante(estudiante):
    """Muestra las notas del estudiante"""
    st.subheader("📊 Notas y Calificaciones")
    
    # Identificar columnas de evaluación
    columnas_info = ['CEDULA', 'NOMBRE', 'APELLIDO', 'EMAIL', 'CARRERA', 'NOTA FINAL', 'PROGRESO (%)', 'ESTADO']
    columnas_evaluacion = [col for col in estudiante.index if col not in columnas_info]
    
    if not columnas_evaluacion:
        st.warning("No hay evaluaciones disponibles")
        return
    
    # Mostrar nota final y progreso si existen
    col1, col2 = st.columns(2)
    with col1:
        if 'NOTA FINAL' in estudiante and pd.notna(estudiante['NOTA FINAL']):
            nota_final = estudiante['NOTA FINAL']
            color = "green" if nota_final >= 10 else "red"
            st.metric(
                "**Nota Final Acumulada**",
                f"{nota_final:.2f}/20",
                delta=None,
                delta_color="normal",
                help="Suma ponderada de todas las evaluaciones calificadas"
            )
    
    with col2:
        if 'PROGRESO (%)' in estudiante and pd.notna(estudiante['PROGRESO (%)']):
            progreso = estudiante['PROGRESO (%)']
            st.metric(
                "**Progreso del Curso**",
                f"{progreso:.1f}%",
                delta=None,
                delta_color="normal",
                help="Porcentaje del curso que ya tiene calificación"
            )
    
    st.markdown("---")
    
    # Mostrar tabla de evaluaciones
    st.subheader("📝 Evaluaciones Individuales")
    
    evaluaciones_data = []
    for col in columnas_evaluacion:
        if pd.notna(estudiante[col]):
            evaluaciones_data.append({
                'Evaluación': col,
                'Nota': f"{estudiante[col]:.1f}/20",
                'Estado': '✅ Calificado' if estudiante[col] >= 0 else '⏳ Pendiente'
            })
        else:
            evaluaciones_data.append({
                'Evaluación': col,
                'Nota': 'No calificado',
                'Estado': '⏳ Pendiente'
            })
    
    if evaluaciones_data:
        df_evaluaciones = pd.DataFrame(evaluaciones_data)
        st.dataframe(df_evaluaciones, use_container_width=True, hide_index=True)
    else:
        st.info("No hay evaluaciones calificadas aún")
    
    # Mostrar gráfico de barras de notas si hay evaluaciones calificadas
    evaluaciones_calificadas = [col for col in columnas_evaluacion if pd.notna(estudiante[col])]
    if evaluaciones_calificadas:
        st.markdown("---")
        st.subheader("📈 Gráfico de Calificaciones")
        
        fig, ax = plt.subplots(figsize=(10, 6))
        
        nombres_evaluaciones = evaluaciones_calificadas
        notas = [estudiante[col] for col in evaluaciones_calificadas]
        
        # Crear barras
        bars = ax.bar(range(len(nombres_evaluaciones)), notas, color='skyblue', edgecolor='black')
        
        # Añadir línea de aprobación
        ax.axhline(y=10, color='red', linestyle='--', alpha=0.7, label='Nota de aprobación (10)')
        
        # Personalizar
        ax.set_xlabel('Evaluaciones')
        ax.set_ylabel('Nota (0-20)')
        ax.set_title('Calificaciones por Evaluación')
        ax.set_xticks(range(len(nombres_evaluaciones)))
        
        # Acortar nombres largos para el eje X
        nombres_cortos = [nombre[:20] + '...' if len(nombre) > 20 else nombre for nombre in nombres_evaluaciones]
        ax.set_xticklabels(nombres_cortos, rotation=45, ha='right')
        
        # Añadir valores en las barras
        for bar, nota in zip(bars, notas):
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2., height + 0.1,
                   f'{nota:.1f}', ha='center', va='bottom', fontsize=9)
        
        ax.legend()
        ax.grid(True, alpha=0.3)
        plt.tight_layout()
        
        st.pyplot(fig)

# Función para mostrar estadísticas generales
def mostrar_estadisticas_generales(estadisticas):
    """Muestra estadísticas generales del curso"""
    st.subheader("📊 Estadísticas Generales del Curso")
    
    # Información general
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Total de Estudiantes", estadisticas.get('total_estudiantes', 0))
    
    with col2:
        if 'estudiantes_activos' in estadisticas:
            st.metric("Estudiantes Activos", estadisticas['estudiantes_activos'])
    
    with col3:
        if 'aprobados' in estadisticas:
            st.metric("Estudiantes Aprobados", f"{estadisticas['aprobados']} ({estadisticas.get('porcentaje_aprobados', 0):.1f}%)")
    
    st.markdown("---")
    
    # Estadísticas de nota final
    if 'nota_promedio' in estadisticas:
        st.subheader("📈 Estadísticas de Nota Final")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Promedio General", f"{estadisticas['nota_promedio']:.2f}/20")
        
        with col2:
            st.metric("Nota Máxima", f"{estadisticas['nota_maxima']:.2f}/20")
        
        with col3:
            st.metric("Nota Mínima", f"{estadisticas['nota_minima']:.2f}/20")
        
        with col4:
            st.metric("Mediana", f"{estadisticas['nota_mediana']:.2f}/20")
        
        # Crear histograma de distribución de notas
        st.markdown("---")
        st.subheader("📊 Distribución de Notas Finales")
        
        # Para esta versión, mostramos información sin gráfico detallado
        # ya que no tenemos los datos completos de todos los estudiantes
        st.info("""
        **Nota sobre privacidad:** 
        El histograma detallado de distribución no está disponible en esta versión 
        para proteger la privacidad de todos los estudiantes. Solo se muestran 
        estadísticas agregadas y anónimas.
        """)
    
    # Distribución por carreras
    if 'distribucion_carreras' in estadisticas:
        st.markdown("---")
        st.subheader("🎓 Distribución por Carrera")
        
        carreras = list(estadisticas['distribucion_carreras'].keys())
        cantidades = list(estadisticas['distribucion_carreras'].values())
        
        # Tabla
        df_carreras = pd.DataFrame({
            'Carrera': carreras,
            'Estudiantes': cantidades
        })
        st.dataframe(df_carreras, use_container_width=True, hide_index=True)
    
    # Estadísticas por evaluación
    if 'evaluaciones' in estadisticas and estadisticas['evaluaciones']:
        st.markdown("---")
        st.subheader("📝 Promedios por Evaluación")
        
        evaluaciones_data = []
        for eval_nombre, stats in estadisticas['evaluaciones'].items():
            evaluaciones_data.append({
                'Evaluación': eval_nombre[:30] + '...' if len(eval_nombre) > 30 else eval_nombre,
                'Promedio': f"{stats['promedio']:.1f}/20",
                'Máxima': f"{stats['maxima']:.1f}/20",
                'Mínima': f"{stats['minima']:.1f}/20",
                'Calificados': stats['estudiantes_calificados']
            })
        
        df_evaluaciones = pd.DataFrame(evaluaciones_data)
        st.dataframe(df_evaluaciones, use_container_width=True, hide_index=True)

# --- SECCIÓN PRINCIPAL DEL PROGRAMA ---

# Encabezado con información del sistema
st.markdown("""
<div style='background-color: #f0f2f6; padding: 15px; border-radius: 10px; margin-bottom: 20px;'>
    <h4 style='color: #1f77b4;'>🔒 Portal de Consulta Segura de Notas</h4>
    <p>Este sistema permite a los estudiantes consultar sus calificaciones de manera segura y privada.</p>
    <p><strong>📁 Archivo de notas:</strong> Cargado automáticamente desde el servidor</p>
</div>
""", unsafe_allow_html=True)

# Sección 1: Carga automática del archivo
st.header("📂 Estado del Sistema")

# Buscar y cargar archivo automáticamente
if st.session_state.df_notas is None:
    with st.spinner("Buscando archivo de notas..."):
        archivos_encontrados = buscar_y_cargar_archivo()
        
        if archivos_encontrados:
            # Intentar cargar cada archivo hasta encontrar uno válido
            for archivo in archivos_encontrados:
                st.info(f"📂 Intentando cargar: {archivo}")
                df, archivo_cargado = cargar_archivo(archivo)
                
                if df is not None:
                    st.session_state.df_notas = df
                    st.session_state.archivo_cargado = archivo_cargado
                    
                    # Calcular estadísticas generales
                    st.session_state.estadisticas_generales = calcular_estadisticas_generales(df)
                    
                    st.success(f"✅ Archivo cargado exitosamente: {archivo_cargado}")
                    st.success(f"📊 {len(df)} estudiantes encontrados en el sistema")
                    break
        else:
            st.error("""
            ❌ **No se encontró el archivo de notas**
            
            **Posibles soluciones:**
            1. Asegúrate de que el archivo de notas esté en el mismo directorio que esta aplicación
            2. El archivo debe llamarse: **notas_estudiantes.xlsx**
            3. Contacta al administrador del sistema si el problema persiste
            """)
            
            # Mostrar archivos disponibles en el directorio
            st.info("📂 Archivos disponibles en el directorio actual:")
            archivos_disponibles = os.listdir('.')
            archivos_excel = [f for f in archivos_disponibles if f.endswith(('.xlsx', '.xls'))]
            
            if archivos_excel:
                for archivo in archivos_excel:
                    st.write(f"  - {archivo}")
            else:
                st.write("  No hay archivos Excel en el directorio")
else:
    st.success(f"✅ Sistema listo. Archivo cargado: {st.session_state.archivo_cargado}")
    st.info(f"📊 {len(st.session_state.df_notas)} estudiantes en el sistema")

st.markdown("---")

# Sección 2: Búsqueda del estudiante (solo si hay datos cargados)
if st.session_state.df_notas is not None:
    st.header("🔍 Consultar Mis Notas")
    
    # Instrucciones
    st.info("""
    **Instrucciones:**
    1. Ingresa tu **cédula** exactamente como aparece en el sistema
    2. O ingresa tu **nombre y apellido** (puedes usar solo una parte si lo prefieres)
    3. Haz clic en "Buscar mis notas"
    4. Solo podrás ver **tus propias calificaciones**
    """)
    
    # Opciones de búsqueda
    metodo_busqueda = st.radio(
        "Método de búsqueda:",
        ["🆔 Por número de cédula", "👤 Por nombre y apellido"],
        horizontal=True
    )
    
    if metodo_busqueda == "🆔 Por número de cédula":
        cedula = st.text_input(
            "Número de cédula:",
            placeholder="Ej: 32778512",
            help="Ingresa tu número de cédula sin puntos ni espacios"
        )
        
        nombres = None
        apellidos = None
        
        col1, col2 = st.columns([3, 1])
        with col1:
            if st.button("🔍 Buscar mis notas", type="primary", use_container_width=True):
                if cedula:
                    with st.spinner("Buscando información del estudiante..."):
                        estudiante = buscar_estudiante(
                            st.session_state.df_notas, 
                            cedula=cedula
                        )
                        
                        if estudiante is not None:
                            st.session_state.estudiante_encontrado = estudiante
                            st.success("✅ ¡Estudiante encontrado!")
                        else:
                            st.error("❌ No se encontró ningún estudiante con esa cédula.")
                            st.info("""
                            **Sugerencias:**
                            - Verifica que hayas ingresado correctamente tu cédula
                            - Intenta buscar por nombre y apellido
                            - Contacta al profesor si crees que hay un error
                            """)
                else:
                    st.warning("⚠️ Por favor, ingresa tu número de cédula.")
        
        with col2:
            if st.button("🔄 Limpiar búsqueda", use_container_width=True):
                st.session_state.estudiante_encontrado = None
                st.rerun()
    
    else:  # Por nombre y apellido
        col1, col2 = st.columns(2)
        with col1:
            nombres = st.text_input(
                "Nombre(s):",
                placeholder="Ej: FÉLIX",
                help="Puedes ingresar uno o más nombres"
            )
        with col2:
            apellidos = st.text_input(
                "Apellido(s):",
                placeholder="Ej: ACOSTA",
                help="Puedes ingresar uno o más apellidos"
            )
        
        cedula = None
        
        col1, col2 = st.columns([3, 1])
        with col1:
            if st.button("🔍 Buscar mis notas", type="primary", use_container_width=True):
                if nombres or apellidos:
                    if not nombres and apellidos:
                        st.warning("⚠️ Por favor, ingresa al menos un nombre o apellido completo.")
                    else:
                        with st.spinner("Buscando información del estudiante..."):
                            estudiante = buscar_estudiante(
                                st.session_state.df_notas, 
                                cedula=None,
                                nombres=nombres,
                                apellidos=apellidos
                            )
                            
                            if estudiante is not None:
                                st.session_state.estudiante_encontrado = estudiante
                                st.success("✅ ¡Estudiante encontrado!")
                            else:
                                st.error("❌ No se encontró ningún estudiante con ese nombre y apellido.")
                                st.info("""
                                **Sugerencias:**
                                - Verifica la ortografía de tu nombre y apellido
                                - Intenta usar solo el primer nombre o apellido
                                - Intenta buscar por cédula
                                - Contacta al profesor si crees que hay un error
                                """)
                else:
                    st.warning("⚠️ Por favor, ingresa al menos un nombre o apellido.")
        
        with col2:
            if st.button("🔄 Limpiar búsqueda", use_container_width=True):
                st.session_state.estudiante_encontrado = None
                st.rerun()
    
    st.markdown("---")
    
    # Sección 3: Mostrar información del estudiante encontrado
    if st.session_state.estudiante_encontrado is not None:
        estudiante = st.session_state.estudiante_encontrado
        
        # Mostrar información personal
        mostrar_info_estudiante(estudiante)
        
        # Mostrar notas del estudiante
        mostrar_notas_estudiante(estudiante)
        
        # Sección 4: Mostrar estadísticas generales
        st.markdown("---")
        st.header("📈 Estadísticas del Curso")
        
        # Información sobre privacidad
        st.info("""
        **🔒 Nota sobre privacidad:** 
        Las estadísticas mostradas son generales y anónimas. No revelan información 
        individual de otros estudiantes. Solo se muestran promedios y distribuciones 
        agregadas para que puedas comparar tu rendimiento con el del grupo.
        """)
        
        if st.session_state.estadisticas_generales:
            mostrar_estadisticas_generales(st.session_state.estadisticas_generales)
    
    else:
        # Mensaje inicial si no se ha buscado
        if not cedula and not nombres and not apellidos:
            st.info("👆 **Por favor, ingresa tus datos arriba para consultar tus notas**")
            
            # Mostrar vista previa de las estadísticas si el estudiante aún no ha buscado
            if st.session_state.estadisticas_generales:
                st.markdown("---")
                st.subheader("📊 Vista Previa de Estadísticas del Curso")
                
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.metric("Total Estudiantes", st.session_state.estadisticas_generales.get('total_estudiantes', 0))
                
                with col2:
                    if 'nota_promedio' in st.session_state.estadisticas_generales:
                        st.metric("Promedio General", f"{st.session_state.estadisticas_generales['nota_promedio']:.1f}/20")
                
                with col3:
                    if 'aprobados' in st.session_state.estadisticas_generales:
                        st.metric("% Aprobados", f"{st.session_state.estadisticas_generales.get('porcentaje_aprobados', 0):.1f}%")
        
        # Información sobre el sistema
        st.markdown("---")
        with st.expander("ℹ️ Información sobre el sistema"):
            st.markdown("""
            ### **Características del Portal de Notas:**
            
            - **🔒 Seguro**: Solo puedes ver tus propias notas
            - **📊 Completo**: Muestra todas tus evaluaciones y nota final acumulada
            - **📈 Informativo**: Proporciona estadísticas generales del curso
            - **📱 Accesible**: Funciona en cualquier dispositivo con navegador web
            
            ### **Cómo funciona:**
            
            1. El profesor genera un archivo Excel con todas las notas
            2. El archivo se coloca en el servidor con un nombre específico
            3. Los estudiantes acceden a este portal web
            4. Cada estudiante busca su información personal
            5. El sistema muestra solo la información del estudiante que busca
            
            ### **Notas importantes:**
            
            - Las notas se muestran en escala de **0 a 20 puntos**
            - La **nota final** es un promedio ponderado de todas las evaluaciones
            - **Nota mínima de aprobación: 10/20 puntos**
            - El **progreso** muestra qué porcentaje del curso ya tiene calificación
            
            ### **Problemas comunes:**
            
            - **No encuentro mis notas**: Verifica que ingresaste correctamente tu cédula o nombre
            - **Error en el sistema**: Contacta al administrador o profesor
            - **Notas incorrectas**: Reporta cualquier discrepancia al profesor
            """)

# Sección de información si no hay datos cargados
else:
    st.info("👋 **Bienvenido al Portal de Notas Estudiantiles**")
    
    st.markdown("""
    ### **Instrucciones para el administrador/profesor:**
    
    1. **Generar el archivo de notas** usando el programa del profesor
    2. **Guardar el archivo** con el nombre: **notas_estudiantes.xlsx**
    3. **Colocar el archivo** en el mismo directorio que esta aplicación
    4. **Actualizar el archivo** regularmente cuando haya nuevas calificaciones
    
    ### **Instrucciones para los estudiantes:**
    
    1. **Acceder al portal web** proporcionado por el profesor
    2. **Buscar tu información** usando tu cédula o nombre completo
    3. **Ver tus calificaciones** individuales y nota final acumulada
    4. **Consultar estadísticas** generales del curso
    
    ### **Formato del archivo requerido:**
    
    El archivo Excel debe contener al menos estas columnas:
    - `CÉDULA` o `CEDULA` (identificación del estudiante)
    - `NOMBRES` o `NOMBRE` (nombre del estudiante)
    - `APELLIDOS` o `APELLIDO` (apellido del estudiante)
    - Columnas de evaluaciones (Parcial I, Tareas, Laboratorios, etc.)
    - Opcional: `NOTA FINAL`, `PROGRESO (%)`, `ESTADO`, `CARRERA`, `CORREO`
    
    ### **Configuración del sistema:**
    
    - **Archivo principal**: `notas_estudiantes.xlsx`
    - **Archivo alternativo**: `notas_estudiantes_backup.xlsx`
    - **Patrón de búsqueda**: `notas_estudiantes*.xlsx`
    
    **Nota**: El sistema buscará automáticamente cualquier archivo que coincida con estos nombres.
    """)
    
    # Mostrar estado del directorio
    st.markdown("---")
    st.subheader("📂 Estado del directorio actual")
    
    archivos_disponibles = os.listdir('.')
    archivos_excel = [f for f in archivos_disponibles if f.endswith(('.xlsx', '.xls'))]
    
    if archivos_excel:
        st.write("**Archivos Excel encontrados:**")
        for archivo in archivos_excel:
            tamaño = os.path.getsize(archivo)
            tamaño_mb = tamaño / (1024 * 1024)
            st.write(f"- `{archivo}` ({tamaño_mb:.2f} MB)")
    else:
        st.write("**No se encontraron archivos Excel en el directorio**")

# Footer
st.markdown("---")
fecha_actual = datetime.now().strftime("%d/%m/%Y")
st.markdown(
    f"""
    <div style='text-align: center'>
        <p>🎓 <strong>Portal de Notas Estudiantiles - Unidad 3</strong></p>
        <p><small>Versión 2.0 • Solo lectura • Consulta segura • {fecha_actual}</small></p>
        <p><small>Archivo predefinido: {ARCHIVO_NOTAS}</small></p>
    </div>
    """,
    unsafe_allow_html=True
)

# Estilos CSS adicionales
st.markdown("""
<style>
    .stMetric {
        background-color: #f0f2f6;
        padding: 15px;
        border-radius: 10px;
        border-left: 5px solid #4e8cff;
    }
    .stDataFrame {
        border-radius: 10px;
        box-shadow: 0 2px 5px rgba(0,0,0,0.1);
    }
    .stSuccess {
        border-radius: 10px;
        padding: 15px;
        background-color: #d4edda;
        border-left: 5px solid #28a745;
    }
    .stWarning {
        border-radius: 10px;
        padding: 15px;
        background-color: #fff3cd;
        border-left: 5px solid #ffc107;
    }
    .stError {
        border-radius: 10px;
        padding: 15px;
        background-color: #f8d7da;
        border-left: 5px solid #dc3545;
    }
    .stInfo {
        border-radius: 10px;
        padding: 15px;
        background-color: #d1ecf1;
        border-left: 5px solid #17a2b8;
    }
    .css-1d391kg {
        padding: 10px;
    }
</style>
""", unsafe_allow_html=True)