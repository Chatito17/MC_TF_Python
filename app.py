import streamlit as st
import networkx as nx
from pyvis.network import Network
import streamlit.components.v1 as components
import pandas as pd

# Configuración de la página
st.set_page_config(layout="wide", page_title="Componentes Conexas")

st.markdown("""
    <style>
        .block-container { padding-top: 1rem; padding-bottom: 0rem; max-width: 95%; }
        header { visibility: hidden; }
        #MainMenu { visibility: hidden; }
        footer { visibility: hidden; }
        .stButton>button { width: 100%; padding: 0.2rem; }
        .stSelectbox>div>div>div { padding: 0.2rem; }
        h1, h2, h3 { margin-top: 0; padding-top: 0; }
    </style>
""", unsafe_allow_html=True)

# Estados del grafo
if 'grafo' not in st.session_state:
    st.session_state.grafo = nx.DiGraph()
    st.session_state.grafo.add_nodes_from(range(6)) # Agregamos 6 nodos por default
if 'paso' not in st.session_state:
    st.session_state.paso = 0

# Algoritmo
def calcular_todas_las_matrices(G):
    nodos = list(G.nodes())
    n = len(nodos)
    if n == 0: return None
        
    # Paso 0: Adyacencia original
    M_orig = [[1 if G.has_edge(u, v) else 0 for v in nodos] for u in nodos]
                
    # Paso 1: 1s en la diagonal
    M_diag = [fila[:] for fila in M_orig]
    for i in range(n): M_diag[i][i] = 1
        
    # Paso 2: Floyd-Warshall (Caminos)
    M_cam = [fila[:] for fila in M_diag]
    for k in range(n):
        for i in range(n):
            for j in range(n):
                M_cam[i][j] = M_cam[i][j] or (M_cam[i][k] and M_cam[k][j])
                
    # Paso 3 y 4: Ordenar filas y columnas
    datos_filas = []
    for i in range(n):
        cant = sum(M_cam[i])
        primer = M_cam[i].index(1) if 1 in M_cam[i] else n 
        datos_filas.append({'idx': i, 'cant': cant, 'primer': primer, 'nodo': nodos[i]})
        
    datos_filas.sort(key=lambda x: (-x['cant'], x['primer']))
    nuevo_orden = [d['idx'] for d in datos_filas]
    nodos_ord = [d['nodo'] for d in datos_filas]
    
    M_filas = [M_cam[i][:] for i in nuevo_orden]
    M_final = [[M_filas[i][j] for j in nuevo_orden] for i in range(n)]
    
    # Extraer componentes conexas reales
    visitados = set()
    componentes = []
    for i in range(n):
        if nodos_ord[i] not in visitados:
            comp = [nodos_ord[j] for j in range(n) if M_final[i][j] == 1 and M_final[j][i] == 1]
            if comp:
                componentes.append(comp)
                visitados.update(comp)

    return {
        'orig': M_orig, 'diag': M_diag, 'cam': M_cam, 'filas': M_filas, 'final': M_final,
        'nodos': nodos, 'nodos_ord': nodos_ord, 'componentes': componentes
    }

# Dibujar el grafo
def mostrar_grafo(G, componentes=None):
    net = Network(height='300px', width='100%', directed=True, bgcolor='#ffffff', font_color='white')
    
    colores = ['#E74C3C', '#2ECC71', '#9B59B6', '#F1C40F', '#1ABC9C', '#E67E22', '#34495E']
    color_map = {}
    if componentes:
        for idx, comp in enumerate(componentes):
            c = colores[idx % len(colores)]
            for nodo in comp: color_map[nodo] = c

    for nodo in G.nodes():
        color = color_map.get(nodo, '#85C1E9')
        net.add_node(nodo, label=str(nodo), color=color)
    for origen, destino in G.edges():
        net.add_edge(origen, destino)
        
    net.set_options('{"physics": {"barnesHut": {"springLength": 80, "springConstant": 0.05}}}')
    net.save_graph("grafo.html")
    with open("grafo.html", "r", encoding="utf-8") as f:
        components.html(f.read(), height=310)

# Tabla
def resaltar_unos(val):
    return 'background-color: #2ECC71; color: white; font-weight: bold;' if val == 1 else 'color: #D3D3D3;'

def aplicar_estilo(df):
    try:
        return df.style.map(resaltar_unos)
    except AttributeError:
        return df.style.applymap(resaltar_unos)

# Interfaz
st.markdown("## Análisis Interactivo de Componentes Conexas")

datos = calcular_todas_las_matrices(st.session_state.grafo)

col_izq, col_der = st.columns([1.2, 2])

# Configuracion grafo
with col_izq:
    st.markdown("#### 1. Configuración del Grafo")
    
    n_nodos = st.number_input("Cantidad de Nodos [4-12]:", min_value=4, max_value=12, value=len(st.session_state.grafo.nodes))
    if n_nodos != len(st.session_state.grafo.nodes):
        st.session_state.grafo = nx.empty_graph(n_nodos, create_using=nx.DiGraph)
        st.session_state.paso = 0
        st.rerun()

    t_rnd, t_man = st.tabs(["Aleatorio", "Manual"])
    with t_rnd:
        if st.button("Generar Aleatorio"):
            st.session_state.grafo = nx.gnp_random_graph(n_nodos, 0.25, directed=True)
            st.session_state.paso = 0
            st.rerun()
            
    with t_man:
        c1, c2, c3 = st.columns([1, 1, 1.2])
        with c1: orig = st.selectbox("Origen", range(n_nodos))
        with c2: dest = st.selectbox("Destino", range(n_nodos))
        with c3:
            if st.button("Unir"):
                st.session_state.grafo.add_edge(orig, dest)
                st.session_state.paso = 0
                st.rerun()
            if st.button("Quitar"):
                if st.session_state.grafo.has_edge(orig, dest):
                    st.session_state.grafo.remove_edge(orig, dest)
                    st.session_state.paso = 0
                    st.rerun()

    st.markdown("#### Vista del Grafo")
    comp_a_pintar = datos['componentes'] if st.session_state.paso == 5 else None
    mostrar_grafo(st.session_state.grafo, comp_a_pintar)

# Ejcución del algoritmo
with col_der:
    st.markdown("#### 2. Ejecución del Algoritmo")
    
    b1, b2, b3 = st.columns([1, 2, 1])
    with b1:
        if st.button("Anterior") and st.session_state.paso > 0:
            st.session_state.paso -= 1
            st.rerun()
    with b2:
        st.markdown(f"<h5 style='text-align: center; color: #3498DB;'>Paso {st.session_state.paso} de 5</h5>", unsafe_allow_html=True)
    with b3:
        if st.button("Siguiente") and st.session_state.paso < 5:
            st.session_state.paso += 1
            st.rerun()

    if datos is not None:
        p = st.session_state.paso
        nodos = datos['nodos']
        nodos_ord = datos['nodos_ord']
        
        if p == 0:
            st.info("**Paso 0: Matriz de Adyacencia.** Muestra las conexiones directas del grafo sin cambios.")
            df = pd.DataFrame(datos['orig'], index=nodos, columns=nodos)
            st.dataframe(aplicar_estilo(df), height=250, use_container_width=True)
            
        elif p == 1:
            st.info("**Paso 1: Diagonal de Unos.** Agregamos `1`s en la diagonal si es necesario.")
            df = pd.DataFrame(datos['diag'], index=nodos, columns=nodos)
            st.dataframe(aplicar_estilo(df), height=250, use_container_width=True)
            
        elif p == 2:
            st.info("**Paso 2: Matriz de Caminos (Floyd-Warshall).** Calculamos todas las conexiones transitivas.")
            df = pd.DataFrame(datos['cam'], index=nodos, columns=nodos)
            st.dataframe(aplicar_estilo(df), height=250, use_container_width=True)
            
        elif p == 3:
            st.info("**Paso 3: Ordenamiento de Filas.** Contamos los `1`s por fila y las ordenamos de mayor a menor.")
            df = pd.DataFrame(datos['filas'], index=nodos_ord, columns=nodos) 
            st.dataframe(aplicar_estilo(df), height=250, use_container_width=True)
            
        elif p == 4:
            st.info("**Paso 4: Ordenamiento de Columnas.** Ordenamos tambien por columnas, y los bloques cuadrados diagonales serán componentes conexas.")
            df = pd.DataFrame(datos['final'], index=nodos_ord, columns=nodos_ord)
            st.dataframe(aplicar_estilo(df), height=250, use_container_width=True)
            
        elif p == 5:
            st.success("**Paso 5: Componentes Conexas.** Se muestran las componentes conexas coloreadas.")
            comps = datos['componentes']
            st.write(f"📊 **Número total de componentes conexas:** `{len(comps)}`")
            
            col_res_izq, col_res_der = st.columns([1, 1.2]) 
            
            with col_res_izq:
                c_cols = st.columns(2) 
                for idx, comp in enumerate(comps):
                    with c_cols[idx % 2]:
                        st.markdown(f"**Grupo {idx+1}:**<br/>{comp}", unsafe_allow_html=True)
                        st.markdown("<br/>", unsafe_allow_html=True)
            
            with col_res_der:
                st.markdown("**Matriz Final:**")
                df = pd.DataFrame(datos['final'], index=nodos_ord, columns=nodos_ord)
                st.dataframe(aplicar_estilo(df), height=280)