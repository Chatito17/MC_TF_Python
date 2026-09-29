import streamlit as st
import networkx as nx
from pyvis.network import Network
import streamlit.components.v1 as components
import random

# --- CONFIGURACIÓN INICIAL ---
st.set_page_config(layout="wide", page_title="Visualizador de Componentes Fuertemente Conexas")

# Inicializar variables de sesión si no existen
if 'grafo' not in st.session_state:
    st.session_state.grafo = nx.DiGraph()
if 'estados' not in st.session_state:
    st.session_state.estados = []
if 'paso_actual' not in st.session_state:
    st.session_state.paso_actual = 0

# --- LÓGICA DEL ALGORITMO (KOSARAJU) CON CAPTURA DE ESTADOS ---
def generar_estados_kosaraju(G):
    estados = []
    colores = {n: '#CCCCCC' for n in G.nodes()} # Gris por defecto
    aristas_actuales = list(G.edges())
    
    def guardar_estado(msg):
        # Guardamos una copia exacta de colores y aristas en este momento
        estados.append({
            "colores": colores.copy(),
            "aristas": list(aristas_actuales),
            "msg": msg
        })

    guardar_estado("Inicio: Grafo original.")

    # Fase 1: DFS para llenar la pila
    visitados = set()
    pila = []
    
    def dfs1(v):
        visitados.add(v)
        colores[v] = '#F5B041' # Naranja: Visitando
        guardar_estado(f"Fase 1: Visitando nodo {v}")
        for vecino in G.successors(v):
            if vecino not in visitados:
                dfs1(vecino)
        pila.append(v)
        colores[v] = '#85C1E9' # Azul: Terminado
        guardar_estado(f"Fase 1: Nodo {v} explorado completamente. Añadido a la pila.")

    for nodo in G.nodes():
        if nodo not in visitados:
            dfs1(nodo)

    # Fase 2: Grafo Traspuesto
    aristas_actuales = [(v, u) for (u, v) in aristas_actuales] # Invertimos aristas para visualización
    colores = {n: '#CCCCCC' for n in G.nodes()} # Reseteamos colores
    guardar_estado("Fase 2: Se invierten las aristas del grafo (Grafo Traspuesto) y reseteamos nodos.")

    # Fase 3: Segundo DFS para encontrar SCC
    visitados.clear()
    GT = G.reverse()
    
    # Paleta de colores para las componentes
    paleta_scc = ['#E74C3C', '#2ECC71', '#9B59B6', '#F1C40F', '#1ABC9C', '#E67E22', '#34495E']
    scc_count = 0

    def dfs2(v, color_scc):
        visitados.add(v)
        colores[v] = color_scc
        guardar_estado(f"Fase 3: Añadiendo nodo {v} al Componente Conexo actual.")
        for vecino in GT.successors(v):
            if vecino not in visitados:
                dfs2(vecino, color_scc)

    while pila:
        nodo = pila.pop()
        if nodo not in visitados:
            color_actual = paleta_scc[scc_count % len(paleta_scc)]
            dfs2(nodo, color_actual)
            scc_count += 1
            guardar_estado(f"Fase 3: ¡Componente Fuertemente Conexa {scc_count} completada!")

    guardar_estado("¡Algoritmo finalizado! Los colores iguales representan nodos en la misma componente.")
    return estados

# --- FUNCION PARA RENDERIZAR PYVIS ---
def mostrar_grafo(nodos, aristas, colores):
    net = Network(height='500px', width='100%', directed=True, bgcolor='#ffffff', font_color='black')
    for nodo in nodos:
        net.add_node(nodo, label=str(nodo), color=colores.get(nodo, '#CCCCCC'))
    for origen, destino in aristas:
        net.add_edge(origen, destino)
    
    # Opciones de físicas para que no rebote demasiado
    net.set_options("""
    var options = {
      "physics": {"barnesHut": {"springLength": 100, "springConstant": 0.04}}
    }
    """)
    net.save_graph("grafo.html")
    with open("grafo.html", "r", encoding="utf-8") as f:
        components.html(f.read(), height=550)

# --- INTERFAZ DE USUARIO (UI) ---
st.title("🧩 Visualizador: Componentes Fuertemente Conexas")

# PANEL LATERAL: Controles
with st.sidebar:
    st.header("1. Crear Grafo")
    num_nodos = st.slider("Número de nodos", 4, 12, 6)
    
    tab_auto, tab_manual = st.tabs(["Aleatorio", "Manual"])
    
    with tab_auto:
        if st.button("Generar Grafo Aleatorio"):
            st.session_state.grafo = nx.gnp_random_graph(num_nodos, 0.3, directed=True)
            st.session_state.estados = [] # Resetear
            st.session_state.paso_actual = 0
            
    with tab_manual:
        st.write("Añade aristas al grafo vacío:")
        if st.button("Limpiar Grafo"):
            st.session_state.grafo = nx.DiGraph()
            st.session_state.grafo.add_nodes_from(range(num_nodos))
            st.session_state.estados = []
            
        col1, col2 = st.columns(2)
        with col1: orig = st.selectbox("Origen", range(num_nodos))
        with col2: dest = st.selectbox("Destino", range(num_nodos))
        if st.button("Añadir Arista"):
            st.session_state.grafo.add_edge(orig, dest)
            st.session_state.estados = [] # Requiere recalcular

    st.header("2. Ejecutar")
    if st.button("Calcular Pasos del Algoritmo", type="primary"):
        if len(st.session_state.grafo.nodes) > 0:
            st.session_state.estados = generar_estados_kosaraju(st.session_state.grafo)
            st.session_state.paso_actual = 0

# PANEL PRINCIPAL: Visualización
if not st.session_state.estados:
    st.info("👈 Crea un grafo y presiona 'Calcular Pasos del Algoritmo' en la barra lateral.")
    # Mostrar el grafo actual sin estados
    if len(st.session_state.grafo.nodes) > 0:
        mostrar_grafo(st.session_state.grafo.nodes(), st.session_state.grafo.edges(), {})
else:
    # Controles de avance y retroceso
    col1, col2, col3 = st.columns([1, 3, 1])
    
    with col1:
        if st.button("⬅️ Anterior") and st.session_state.paso_actual > 0:
            st.session_state.paso_actual -= 1
            
    with col3:
        if st.button("Siguiente ➡️") and st.session_state.paso_actual < len(st.session_state.estados) - 1:
            st.session_state.paso_actual += 1

    # Obtener el estado actual
    estado_actual = st.session_state.estados[st.session_state.paso_actual]
    
    with col2:
        st.markdown(f"<h4 style='text-align: center; color: #1f77b4;'>Paso {st.session_state.paso_actual + 1} de {len(st.session_state.estados)}</h4>", unsafe_allow_html=True)
        st.success(estado_actual["msg"])

    # Renderizar el grafo en su estado actual
    mostrar_grafo(st.session_state.grafo.nodes(), estado_actual["aristas"], estado_actual["colores"])