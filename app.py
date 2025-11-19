import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime

# --- CONFIGURACIÓN DE LA PÁGINA ---
st.set_page_config(page_title="DentalCare SQL", page_icon="🦷", layout="wide")

# --- GESTIÓN DE BASE DE DATOS (SQLite) ---

def init_db():
    """Inicializa la base de datos y crea las tablas si no existen."""
    conn = sqlite3.connect('dental.db', check_same_thread=False)
    c = conn.cursor()
    
    # Tabla de Pacientes
    c.execute('''CREATE TABLE IF NOT EXISTS patients
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                  name TEXT, 
                  age INTEGER, 
                  phone TEXT, 
                  status TEXT, 
                  allergies TEXT, 
                  created_at DATE)''')
    
    # Tabla de Historial/Evolución
    c.execute('''CREATE TABLE IF NOT EXISTS history
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                  patient_id INTEGER, 
                  date TEXT, 
                  treatment TEXT, 
                  doctor TEXT,
                  FOREIGN KEY(patient_id) REFERENCES patients(id))''')

    # Tabla de Dientes (Odontograma)
    # Guarda el estado de cada diente para cada paciente
    c.execute('''CREATE TABLE IF NOT EXISTS teeth
                 (patient_id INTEGER, 
                  tooth_id INTEGER, 
                  status TEXT,
                  PRIMARY KEY (patient_id, tooth_id),
                  FOREIGN KEY(patient_id) REFERENCES patients(id))''')
    
    conn.commit()
    return conn

# Conectamos a la DB al iniciar
conn = init_db()

# --- FUNCIONES CRUD (Crear, Leer, Actualizar) ---

def add_patient(name, age, phone, allergies):
    c = conn.cursor()
    c.execute("INSERT INTO patients (name, age, phone, status, allergies, created_at) VALUES (?, ?, ?, ?, ?, ?)",
              (name, age, phone, "Activo", allergies, datetime.now().date()))
    conn.commit()
    return c.lastrowid

def get_all_patients():
    return pd.read_sql("SELECT * FROM patients", conn)

def add_history_note(patient_id, note, doctor="Dr. Principal"):
    c = conn.cursor()
    date_str = datetime.now().strftime("%Y-%m-%d %H:%M")
    c.execute("INSERT INTO history (patient_id, date, treatment, doctor) VALUES (?, ?, ?, ?)",
              (patient_id, date_str, note, doctor))
    conn.commit()

def get_patient_history(patient_id):
    return pd.read_sql("SELECT * FROM history WHERE patient_id = ? ORDER BY id DESC", conn, params=(patient_id,))

def get_tooth_status(patient_id, tooth_id):
    c = conn.cursor()
    c.execute("SELECT status FROM teeth WHERE patient_id = ? AND tooth_id = ?", (patient_id, tooth_id))
    result = c.fetchone()
    if result:
        return result[0]
    return "Sano" # Valor por defecto

def update_tooth_status(patient_id, tooth_id, status):
    c = conn.cursor()
    # Usamos REPLACE para insertar o actualizar si ya existe
    c.execute("REPLACE INTO teeth (patient_id, tooth_id, status) VALUES (?, ?, ?)", 
              (patient_id, tooth_id, status))
    conn.commit()

# --- INTERFAZ DE USUARIO ---

def show_dashboard():
    st.title("📊 Dashboard DentalCare (Versión DB)")
    
    df_patients = get_all_patients()
    total_patients = len(df_patients)
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric(label="Pacientes Registrados", value=total_patients)
    with col2:
        st.metric(label="Citas Hoy", value="3") # Simulado para el ejemplo
    with col3:
        st.info("Base de datos: Conectada ✅")

def show_patients():
    st.title("👥 Gestión de Pacientes")
    
    # Formulario para agregar (en un expander para que no ocupe espacio siempre)
    with st.expander("➕ Agregar Nuevo Paciente"):
        with st.form("new_patient"):
            col_a, col_b = st.columns(2)
            with col_a:
                new_name = st.text_input("Nombre Completo")
                new_age = st.number_input("Edad", min_value=0, max_value=120, value=30)
            with col_b:
                new_phone = st.text_input("Teléfono")
                new_allergies = st.text_input("Alergias (separar por comas)")
            
            submitted = st.form_submit_button("Guardar Paciente")
            if submitted and new_name:
                add_patient(new_name, new_age, new_phone, new_allergies)
                st.success("Paciente guardado en base de datos!")
                st.rerun()

    # Mostrar tabla
    df = get_all_patients()
    if not df.empty:
        st.dataframe(df[['id', 'name', 'age', 'phone', 'status']], use_container_width=True, hide_index=True)
        
        # Selector para ir a detalle
        patient_options = df.set_index('id')['name'].to_dict()
        selected_id = st.selectbox("Selecciona ID de paciente para abrir Ficha:", 
                                   options=[None] + list(patient_options.keys()), 
                                   format_func=lambda x: f"{x} - {patient_options[x]}" if x else "Seleccionar...")
        
        if selected_id:
            st.session_state.current_patient_id = selected_id
            st.session_state.view = 'detail'
            st.rerun()
    else:
        st.info("No hay pacientes. Agrega uno arriba.")

def show_patient_detail():
    # Recuperar datos frescos de la DB
    p_id = st.session_state.current_patient_id
    c = conn.cursor()
    c.execute("SELECT * FROM patients WHERE id = ?", (p_id,))
    patient = c.fetchone()
    # Mapear resultado de tupla a nombres (id, name, age, phone, status, allergies...)
    
    if st.button("⬅️ Volver a la lista"):
        st.session_state.view = 'patients'
        st.rerun()

    st.title(f"Ficha Clínica: {patient[1]}") # patient[1] es el nombre
    
    col_izq, col_der = st.columns([1, 2])

    with col_izq:
        st.markdown("### Datos Personales")
        st.write(f"**Edad:** {patient[2]}")
        st.write(f"**Teléfono:** {patient[3]}")
        
        st.markdown("### ⚠️ Alertas")
        allergies = patient[5]
        if allergies:
            st.error(f"Alergias: {allergies}")
        else:
            st.success("Sin alergias conocidas")

    with col_der:
        tab_odonto, tab_histo = st.tabs(["🦷 Odontograma", "📝 Historial Médico"])
        
        with tab_odonto:
            st.subheader("Odontograma Digital")
            
            c1, c2 = st.columns(2)
            with c1:
                tooth_sel = st.number_input("Seleccionar Diente (1-32)", 1, 32, 1)
            with c2:
                # Obtener estado actual de la DB
                current_status = get_tooth_status(p_id, tooth_sel)
                status_opts = ["Sano", "Caries", "Obturado", "Endodoncia", "Ausente"]
                
                new_status = st.selectbox("Estado del Diente", status_opts, index=status_opts.index(current_status) if current_status in status_opts else 0)
                
                if st.button("Actualizar Diente"):
                    update_tooth_status(p_id, tooth_sel, new_status)
                    st.success("Guardado!")
                    st.rerun()
            
            # Visualización rápida de dientes modificados
            st.caption("Resumen de dientes con tratamiento:")
            teeth_df = pd.read_sql("SELECT tooth_id, status FROM teeth WHERE patient_id = ?", conn, params=(p_id,))
            if not teeth_df.empty:
                 # Colores simples para la tabla
                def color_rows(val):
                    color = 'white'
                    if val == 'Caries': color = '#ffcccc'
                    elif val == 'Obturado': color = '#ccffcc'
                    elif val == 'Ausente': color = '#eeeeee'
                    return f'background-color: {color}'
                
                st.dataframe(teeth_df.style.map(color_rows, subset=['status']), use_container_width=True)
            else:
                st.info("Toda la dentadura registrada como 'Sana'.")

        with tab_histo:
            txt_tratamiento = st.text_area("Evolución / Procedimiento realizado hoy:")
            if st.button("Guardar Nota Clínica"):
                if txt_tratamiento:
                    add_history_note(p_id, txt_tratamiento)
                    st.success("Nota agregada al historial")
                    st.rerun()
            
            st.divider()
            st.subheader("Historial Previo")
            history_df = get_patient_history(p_id)
            if not history_df.empty:
                for _, row in history_df.iterrows():
                    st.text(f"📅 {row['date']} | 👨‍⚕️ {row['doctor']}")
                    st.info(row['treatment'])
            else:
                st.write("Sin historial previo.")

# --- MAIN LOOP ---

if 'view' not in st.session_state:
    st.session_state.view = 'dashboard'

with st.sidebar:
    st.header("🏥 DentalCare SQL")
    menu = st.radio("Ir a:", ["Dashboard", "Pacientes"])
    
    if menu == "Dashboard":
        st.session_state.view = 'dashboard'
    elif menu == "Pacientes" and st.session_state.view != 'detail':
        st.session_state.view = 'patients'

if st.session_state.view == 'dashboard':
    show_dashboard()
elif st.session_state.view == 'patients':
    show_patients()
elif st.session_state.view == 'detail':
    show_patient_detail()
