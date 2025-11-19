import streamlit as st
import pandas as pd
from datetime import datetime

# --- CONFIGURACIÓN DE LA PÁGINA ---
st.set_page_config(page_title="DentalCare CRM", page_icon="🦷", layout="wide")

# --- ESTILOS CSS PERSONALIZADOS (Para que se vea más bonito) ---
st.markdown("""
    <style>
    .big-font { font-size:20px !important; font-weight: bold; }
    .stButton>button { width: 100%; border-radius: 10px; }
    .metric-card { background-color: #f0f2f6; padding: 20px; border-radius: 10px; }
    </style>
    """, unsafe_allow_html=True)

# --- GESTIÓN DEL ESTADO (Base de Datos Simulada) ---
if 'patients' not in st.session_state:
    st.session_state.patients = [
        {"id": 1, "name": "Ana García", "age": 28, "phone": "+56 9 1234 5678", "status": "Activo", "allergies": ["Penicilina"], "history": []},
        {"id": 2, "name": "Carlos Pérez", "age": 35, "phone": "+56 9 8765 4321", "status": "Pendiente", "allergies": [], "history": []},
        {"id": 3, "name": "María Rodríguez", "age": 42, "phone": "+56 9 1122 3344", "status": "Activo", "allergies": ["Latex", "Polen"], "history": []},
    ]

if 'appointments' not in st.session_state:
    st.session_state.appointments = [
        {"id": 1, "patient": "Ana García", "time": "09:00", "type": "Limpieza", "status": "Confirmado"},
        {"id": 2, "patient": "Carlos Pérez", "time": "10:30", "type": "Revisión", "status": "En Espera"},
    ]

# --- DENTIGRAMA / ODONTOGRAMA (Lógica en Python) ---
# Inicializamos el estado de los dientes si no existe
if 'teeth_status' not in st.session_state:
    # 32 dientes, estado inicial 'Sano'
    st.session_state.teeth_status = {i: "Sano" for i in range(1, 33)}

def update_tooth(tooth_id, new_status):
    st.session_state.teeth_status[tooth_id] = new_status

# --- FUNCIONES DE VISTA ---

def show_dashboard():
    st.title("📊 Dashboard DentalCare")
    
    # Métricas
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric(label="Pacientes Totales", value=len(st.session_state.patients), delta="1 nuevo hoy")
    with col2:
        st.metric(label="Citas Hoy", value=len(st.session_state.appointments))
    with col3:
        st.metric(label="Ingresos Mes", value="$4.5M", delta="+12%")

    st.divider()

    # Citas Rápidas
    st.subheader("📅 Próximas Citas")
    df_appointments = pd.DataFrame(st.session_state.appointments)
    st.dataframe(df_appointments, use_container_width=True, hide_index=True)

def show_patients():
    st.title("👥 Gestión de Pacientes")
    
    col_search, col_add = st.columns([3, 1])
    
    with col_search:
        search_term = st.text_input("🔍 Buscar paciente por nombre", "")
    
    with col_add:
        if st.button("➕ Nuevo Paciente"):
            st.session_state.show_add_modal = True

    # Filtrado
    filtered_patients = [p for p in st.session_state.patients if search_term.lower() in p['name'].lower()]
    
    # Mostrar lista como tabla interactiva
    if filtered_patients:
        df = pd.DataFrame(filtered_patients)
        # Seleccionar columnas a mostrar
        display_df = df[['id', 'name', 'phone', 'status', 'last_visit' if 'last_visit' in df else 'status']] 
        
        st.dataframe(display_df, use_container_width=True, hide_index=True)
        
        # Selector para ir a la ficha
        patient_names = [p['name'] for p in filtered_patients]
        selected_patient_name = st.selectbox("Selecciona un paciente para ver su Ficha Clínica:", ["Seleccionar..."] + patient_names)
        
        if selected_patient_name != "Seleccionar...":
            # Encontrar el objeto paciente completo
            selected_patient = next(p for p in filtered_patients if p['name'] == selected_patient_name)
            st.session_state.current_patient = selected_patient
            st.session_state.view = 'detail'
            st.rerun()

def show_patient_detail():
    patient = st.session_state.current_patient
    
    if st.button("⬅️ Volver a la lista"):
        st.session_state.view = 'patients'
        st.rerun()

    st.title(f"Ficha Clínica: {patient['name']}")
    
    col_info, col_clinical = st.columns([1, 2])

    with col_info:
        st.info(f"**Edad:** {patient['age']} años")
        st.success(f"**Estado:** {patient['status']}")
        st.write(f"📞 **Tel:** {patient['phone']}")
        
        st.markdown("### ⚠️ Alertas Médicas")
        if patient['allergies']:
            for allergy in patient['allergies']:
                st.error(f"Alergia: {allergy}")
        else:
            st.write("No registra alergias.")

    with col_clinical:
        tab1, tab2 = st.tabs(["🦷 Odontograma", "📝 Historial"])
        
        with tab1:
            st.subheader("Estado de la Dentadura")
            st.write("Selecciona un diente para cambiar su estado:")
            
            # Grid de selección para Odontograma
            c1, c2 = st.columns(2)
            with c1:
                tooth_id = st.number_input("Número de Diente", min_value=1, max_value=32, value=1)
            with c2:
                status_options = ["Sano", "Caries", "Tratamiento Pendiente", "Ausente", "Corona"]
                current_status = st.session_state.teeth_status[tooth_id]
                new_status = st.selectbox("Estado", status_options, index=status_options.index(current_status))
                
                if new_status != current_status:
                    update_tooth(tooth_id, new_status)
                    st.success(f"Diente {tooth_id} actualizado a {new_status}")

            # Visualización simple del odontograma en una tabla
            teeth_data = [{"Diente": k, "Estado": v} for k, v in st.session_state.teeth_status.items()]
            df_teeth = pd.DataFrame(teeth_data)
            
            # Usamos colores condicionales en la tabla
            def color_coding(val):
                color = 'white'
                if val == 'Caries': color = '#ffcccb' # Rojo claro
                elif val == 'Ausente': color = '#d3d3d3' # Gris
                elif val == 'Tratamiento Pendiente': color = '#add8e6' # Azul claro
                return f'background-color: {color}'

            st.dataframe(df_teeth.style.map(color_coding, subset=['Estado']), use_container_width=True, height=300)

        with tab2:
            st.subheader("Historial de Tratamientos")
            treatment_note = st.text_area("Nueva nota de evolución")
            if st.button("Guardar Evolución"):
                new_record = {
                    "date": datetime.now().strftime("%Y-%m-%d"),
                    "note": treatment_note,
                    "doctor": "Dr. Usuario"
                }
                patient['history'].append(new_record)
                st.success("Nota guardada")
            
            if patient['history']:
                for record in patient['history']:
                    st.text(f"{record['date']} - {record['doctor']}")
                    st.info(record['note'])
            else:
                st.write("No hay historial previo.")

# --- NAVEGACIÓN PRINCIPAL ---

# Inicializar vista
if 'view' not in st.session_state:
    st.session_state.view = 'dashboard'

# Sidebar Menu
with st.sidebar:
    st.header("DentalCare")
    selected = st.radio("Navegación", ["Dashboard", "Pacientes", "Agenda"])
    
    # Sincronizar radio button con estado
    if selected == "Dashboard" and st.session_state.view != 'dashboard':
        st.session_state.view = 'dashboard'
        st.rerun()
    elif selected == "Pacientes" and st.session_state.view not in ['patients', 'detail']:
        st.session_state.view = 'patients'
        st.rerun()
    # (Agenda podría implementarse similar)

# Renderizar vistas
if st.session_state.view == 'dashboard':
    show_dashboard()
elif st.session_state.view == 'patients':
    show_patients()
elif st.session_state.view == 'detail':
    show_patient_detail()
