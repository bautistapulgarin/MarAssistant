# En la sección "MOSTRAR RESULTADOS", modifica el if para incluir el nuevo tipo:
if 'last_query_result' in st.session_state:
    titulo, df_resultado, grafico, tipo_resultado = st.session_state['last_query_result']
    
    st.markdown(f'<div class="mar-card" style="margin-top:20px;"><p style="color:{PALETTE["primary"]}; font-size: 20px; font-weight:700; margin:0 0 8px 0;">{titulo}</p></div>', unsafe_allow_html=True)

    # 🆕 NUEVO TIPO: Restricción de contrato con estructura específica
    if tipo_resultado == 'restriccion_contrato':
        st.markdown(f'<div class="mar-card" style="margin-top:0px;">', unsafe_allow_html=True)
        st.markdown("### Resumen de Campos de Restricción")
        
        # Mostrar la tabla con estilo mejorado
        st.dataframe(
            df_resultado,
            hide_index=True,
            use_container_width=True,
            column_config={
                "Campo": st.column_config.Column("Campo", width="medium"),
                "Valor": st.column_config.TextColumn("Valor", width="large")
            }
        )
        
        # Opcional: Mostrar el resumen concatenado también
        if hasattr(st.session_state, 'ultima_restriccion_procesada'):
            datos = st.session_state.ultima_restriccion_procesada
            resumen_concatenado = f"{datos['proyecto']} + {datos['componente']} + {datos['acuerdo_servicio']} + {datos['detalle']}"
            st.markdown(f"**Resumen concatenado:** `{resumen_concatenado}`")
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    # Los tipos existentes (restricciones, general, etc.)
    elif tipo_resultado == 'restricciones':
        # ... código existente para restricciones ...
