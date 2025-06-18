import streamlit as st
from database import Produto, Movimentacao, TipoMovimentacao, session
from sqlalchemy import func
import pandas as pd
import plotly.express as px
import datetime

st.set_page_config(page_title="Gestão de Estoque", layout="wide")
st.title("📦 Sistema de Gestão de Estoque")

menu = ["📋 Produtos", "📥 Entrada/Saída", "📊 Relatórios"]
escolha = st.sidebar.selectbox("Menu", menu)

# Função para atualizar DataFrame de produtos
def get_estoque_df():
    produtos = session.query(Produto).all()
    return pd.DataFrame([{"ID": p.id, "Produto": p.nome, "Quantidade": p.quantidade} for p in produtos])

# Página Produtos
if escolha == "📋 Produtos":
    st.subheader("Cadastro de Produtos")

    with st.form("form_produto"):
        nome = st.text_input("Nome do Produto")
        submitted = st.form_submit_button("Adicionar")
        if submitted and nome:
            novo_produto = Produto(nome=nome)
            session.add(novo_produto)
            session.commit()
            st.success(f"Produto '{nome}' adicionado com sucesso!")

    st.subheader("Estoque Atual")
    df = get_estoque_df()
    st.dataframe(df)

    st.subheader("🗑️ Deletar Produto")
    produtos = session.query(Produto).all()
    if produtos:
        produto_nomes = {f"{p.nome} (ID {p.id})": p.id for p in produtos}
        prod_selecionado = st.selectbox("Selecione o produto para deletar", list(produto_nomes.keys()))

        if st.button("Deletar Produto", use_container_width=True, type="primary"):
            pid = produto_nomes[prod_selecionado]

            # Verifica se há movimentações vinculadas
            movimentos = session.query(Movimentacao).filter_by(produto_id=pid).first()
            if movimentos:
                st.error("❌ Este produto possui movimentações e não pode ser deletado.")
            else:
                session.query(Produto).filter_by(id=pid).delete()
                session.commit()
                st.success("✅ Produto deletado com sucesso.")
                st.rerun()
    else:
        st.info("Nenhum produto cadastrado.")

# Página Entrada/Saída
elif escolha == "📥 Entrada/Saída":
    st.subheader("Registrar Entrada ou Saída")

    produtos = session.query(Produto).all()
    produto_dict = {f"{p.nome} (ID {p.id})": p.id for p in produtos}

    with st.form("form_movimentacao"):
        produto_nome = st.selectbox("Produto", list(produto_dict.keys()))
        tipo = st.radio("Tipo", [TipoMovimentacao.entrada, TipoMovimentacao.saida])
        quantidade = st.number_input("Quantidade", min_value=1)
        data = st.date_input("Data", value=datetime.date.today())
        submitted = st.form_submit_button("Registrar")

        if submitted:
            pid = produto_dict[produto_nome]
            produto = session.query(Produto).filter_by(id=pid).first()

            if tipo == TipoMovimentacao.saida and produto.quantidade < quantidade:
                st.error("Estoque insuficiente para saída.")
            else:
                mov = Movimentacao(produto_id=pid, tipo=tipo, quantidade=quantidade, data=data)
                session.add(mov)
                if tipo == TipoMovimentacao.entrada:
                    produto.quantidade += quantidade
                else:
                    produto.quantidade -= quantidade
                session.commit()
                st.success("Movimentação registrada!")

    st.subheader("Histórico de Movimentações")
    movs = session.query(Movimentacao).all()
    dados = [
        {
            "ID": m.id,
            "Produto": session.query(Produto).get(m.produto_id).nome,
            "Tipo": m.tipo.value,
            "Quantidade": m.quantidade,
            "Data": m.data,
        } for m in movs
    ]
    st.dataframe(pd.DataFrame(dados))

    # Deletar movimentações
    st.subheader("🗑️ Deletar Movimentação")
    if movs:
        mov_opcoes = {
            f"{m.id} - {session.query(Produto).get(m.produto_id).nome} ({m.tipo.value}, {m.quantidade}, {m.data})": m.id
            for m in movs
        }

        mov_sel = st.selectbox("Selecione a movimentação", list(mov_opcoes.keys()))

        if st.button("Deletar Movimentação", use_container_width=True):
            mid = mov_opcoes[mov_sel]
            mov = session.query(Movimentacao).get(mid)
            produto = session.query(Produto).get(mov.produto_id)

            if mov.tipo == TipoMovimentacao.entrada:
                produto.quantidade -= mov.quantidade
            else:
                produto.quantidade += mov.quantidade

            session.delete(mov)
            session.commit()
            st.success("✅ Movimentação deletada e estoque ajustado.")
            st.rerun()
    else:
        st.info("Nenhuma movimentação registrada.")

# Página de Relatórios
elif escolha == "📊 Relatórios":
    st.subheader("Análise de Movimentações")

    movs = session.query(Movimentacao).all()
    if not movs:
        st.info("Nenhuma movimentação registrada.")
    else:
        df_mov = pd.DataFrame([{
            "Produto": session.query(Produto).get(m.produto_id).nome,
            "Tipo": m.tipo.value,
            "Quantidade": m.quantidade,
            "Data": m.data
        } for m in movs])

        col1, col2 = st.columns(2)

        with col1:
            st.markdown("### Movimentações por Tipo")
            tipo_group = df_mov.groupby("Tipo")["Quantidade"].sum().reset_index()
            fig_tipo = px.pie(tipo_group, names="Tipo", values="Quantidade", title="Entradas vs Saídas")
            st.plotly_chart(fig_tipo)

        with col2:
            st.markdown("### Movimentações por Produto")
            prod_group = df_mov.groupby("Produto")["Quantidade"].sum().reset_index()
            fig_prod = px.bar(prod_group, x="Produto", y="Quantidade", title="Movimentações Totais por Produto")
            st.plotly_chart(fig_prod)

        st.markdown("### Evolução Temporal")
        df_mov["Data"] = pd.to_datetime(df_mov["Data"])
        df_agg = df_mov.groupby(["Data", "Tipo"])["Quantidade"].sum().reset_index()
        fig_time = px.line(df_agg, x="Data", y="Quantidade", color="Tipo", title="Movimentações ao Longo do Tempo")
        st.plotly_chart(fig_time)
