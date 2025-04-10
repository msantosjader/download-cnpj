# **DownloadCNPJ**

[![Status: Em evolução](https://img.shields.io/badge/status-em%20evolução-blueviolet)]()
[![Python Version](https://img.shields.io/badge/python-3.8%2B-blue)]()
[![License: MIT](https://img.shields.io/badge/license-MIT-green)]()

---

## Índice

- [Descrição](#descrição)  
- [Recursos](#recursos)  
- [Pré‑requisitos](#pré‑requisitos)  
- [Instalação e Execução](#🚀-instalação-e-execução)  
- [Capturas de Tela](#📸-capturas-de-tela)  
- [Estrutura de Pastas](#estrutura-de-pastas)  
- [Contribuição](#contribuição)  
- [Licença](#licença)  

---

## Descrição

O **DownloadCNPJ** é um gerenciador de downloads e atualizações automáticas dos arquivos da base de dados CNPJ, fornecida pela Receita Federal do Brasil.  
Com ele você pode:

- Baixar arquivos por ano e mês  
- Acompanhar status de downloads em andamento  
- Verificar integridade (nome e tamanho do arquivo)  
- Indicar visualmente se o arquivo já foi baixado ou está pendente

---

> ℹ️ Este projeto foi desenvolvido como parte dos meus estudos em Python. Sou iniciante e o desenvolvimento foi feito em ambiente Windows.
> Contou com o apoio de uma I.A. para organização, dúvidas técnicas e geração de documentação.
> Contribuições e sugestões são muito bem-vindas! 🎉

## Recursos

- ✔️ Download e atualização automáticos  
- 🔄 Monitoramento de tarefas em tempo real  
- 🌐 Interface web interativa com NiceGUI  

---

## Pré‑requisitos

- Python 3.8 ou superior  
- Dependências listadas em [requirements.txt](requirements.txt)  
- Conexão à internet para acessar os arquivos da RFB  

---

## 🚀 Instalação e Execução

1. Instale as dependências:
   ```bash
   pip install -r requirements.txt
   ```

2. Execute o aplicativo:
   ```bash
   python main.py
   ```

**📁 Por padrão, os arquivos baixados serão salvos em:**  
`~/Downloads/DownloadCNPJ` *(ou equivalente no Windows: `C:\\Users\\SeuUsuário\\Downloads\\DownloadCNPJ`)*

---

## 📸 Capturas de Tela

### Tela Geral  
<img src="https://i.ibb.co/KpsdXyVq/Captura-de-tela-2025-04-10-175600.png" alt="Tela Geral" width="600"/>

---

### Configurações de Download  
<img src="https://i.ibb.co/8gS95hzS/Captura-de-tela-2025-04-10-175639.png" alt="Configurações" width="300"/>

---

### Downloads em Andamento  
<img src="https://i.ibb.co/BHvW32Wf/Captura-de-tela-2025-04-10-175746.png" alt="Downloads em andamento" width="300"/>

---

### Arquivos Disponíveis  
<img src="https://i.ibb.co/5gJW09mk/Captura-de-tela-2025-04-10-175757.png" alt="Arquivos disponíveis" width="300"/>

---

## 🔄 Em evolução

Este projeto já está funcional, mas tem espaço para melhorias. Ele foi criado para ser utilizado em outros projetos de consulta e análise de dados.
Feedbacks, sugestões e contribuições são muito bem-vindos!

---

## Licença

Este projeto está licenciado sob a [MIT License](LICENSE).  

---

**Fonte dos dados:**  
[Cadastro Nacional da Pessoa Jurídica (CNPJ)](https://dados.gov.br/dados/conjuntos-dados/cadastro-nacional-da-pessoa-juridica---cnpj)
