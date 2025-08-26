# 🎪 Dashboards de Circos — Estilo Power BI (Streamlit)

Este app permite **fazer upload de um Excel ou CSV** como o relatório da Guichê Web e gerar **dashboards interativos** com filtros por **data** e **circo**.

## ▶️ Como rodar localmente

1. Instale as dependências (ideal em um virtualenv):
   ```bash
   pip install -r requirements.txt
   ```
2. Rode o app:
   ```bash
   streamlit run app.py
   ```
3. Abra o link que aparecer no terminal (geralmente http://localhost:8501), envie seu arquivo e explore os gráficos.

## 🚀 Como publicar (grátis) no Streamlit Community Cloud

1. Crie um repositório no GitHub e faça **upload** destes 2 arquivos:
   - `app.py`
   - `requirements.txt`
2. Acesse https://share.streamlit.io/
3. Conecte sua conta GitHub, escolha o repositório e branch, e selecione o arquivo `app.py` como **Main file**.
4. Clique em **Deploy**. Em ~1–2 min seu app estará público, com URL própria para compartilhar.

> Dica: sempre que você fizer commit no GitHub, o Streamlit atualiza o app automaticamente.

## 📄 Formato esperado dos dados

O app detecta automaticamente as colunas mais comuns:
- `Data Evento` (ou qualquer coluna contendo “data”) — será usada para filtros e séries temporais
- `Evento` — usada para derivar o campo **Circo** (o texto antes do caracter `|`)
- Métricas de faturamento (se presente):
  - `Faturamento Total`, `Faturamento Pdv`, `Faturamento Web`
  - `Faturamento Gestão Produtor`, `Faturamento Gestão Empresa`
  - `Total Repasses`, `Total Descontos`, `Taxa Antecipação`, `Taxa Transferencia`
  - Colunas iniciadas com `I:` (insumos/taxas) também são tratadas como numéricas

Mesmo que algumas colunas não existam, o app se adapta e mostra o que for possível.

## 🔒 Privacidade

Os dados enviados ficam apenas na sessão do navegador e memória do servidor do Streamlit do seu app. Não há upload para terceiros além da sua própria implantação.

## 🛠️ Personalizações fáceis

- Quer incluir **mapa por cidade/UF** ou métricas de **ingressos**? Basta adicionar as colunas e criar novos gráficos com Plotly dentro do `app.py`.
- Para padronizar o nome do circo, edite a função `derive_circo`.

---

Feito com ❤️ em Streamlit — dashboards rápidos, bonitos e compartilháveis.