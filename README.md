# **DownloadCNPJ**

[![Status: Em evolução](https://img.shields.io/badge/status-em%20evolução-blueviolet)]()
[![Python Version](https://img.shields.io/badge/python-3.8%2B-blue)]()
[![License: MIT](https://img.shields.io/badge/license-MIT-green)]()

---

O **DownloadCNPJ** é um gerenciador de downloads dos arquivos da base de dados do CNPJ, disponibilizados mensalmente pela Receita Federal do Brasil.

Desenvolvido para facilitar o monitoramento, visualização e download dos arquivos mais recentes, organizados por mês/ano, de forma simples e automatizada, é parte de uma ferramenta mais ampla que estou desenvolvendo para consulta e análise da base de dados do CNPJ.  
Como já está funcional de forma independente, pode ser útil para outras pessoas que trabalham ou precisam lidar com esses dados.

Arquivos: [Receita Federal do Brasil - Dados Abertos CNPJ](https://arquivos.receitafederal.gov.br/dados/cnpj/dados_abertos_cnpj/)

### Funcionalidades principais

- Visualizar arquivos já baixados e os que ainda estão pendentes
- Verificar novos períodos disponibilizados
- Acompanhar o status e progresso dos downloads em tempo real
- Continuar downloads incompletos automaticamente

## Recursos

- Interface interativa via NiceGUI
- Monitoramento em tempo real dos downloads
- Reconhecimento automático de arquivos já existentes
- Atualização dinâmica dos dados disponíveis no portal da RFB
- Configuração personalizável via `settings.py` ou interface gráfica

---

## Pré‑requisitos

- Python 3.8 ou superior  
- Dependências listadas em [`requirements.txt`](requirements.txt)  
- Conexão à internet para acessar os arquivos da RFB  

---

## Instalação e Execução

1. Instale as dependências:
```bash
pip install -r requirements.txt
```

2. Execute o aplicativo:
```bash
python main.py
```

Ou, se preferir, baixe o executável (link será disponibilizado em breve).

---

## Variáveis configuráveis (`settings.py`)

| Constante                   | Padrão                                        | Descrição                                                                                       |
|----------------------------|-----------------------------------------------|--------------------------------------------------------------------------------------------------|
| `ENV`                      | `"dev"`<br>`"prod"`                            | `"dev"` salva o `settings.json` no diretório do projeto<br>`"prod"` usa a pasta de config do sistema |
| `MAX_RETRIES`              | `100`                                          | Máximo de tentativas para baixar um arquivo                                                     |
| `CHUNK_TIMEOUT`            | `60`                                           | Tempo máximo (em segundos) para baixar um pedaço (chunk)                                        |
| `MAX_CONCURRENT_DOWNLOADS` | `10`                                           | Número máximo de downloads concorrentes                                                         |
| `CHUNK_SIZE`               | `10 * 1024 * 1024 (10 MB)`                     | Tamanho de cada chunk baixado. Aumente para downloads mais rápidos, reduza para menor consumo  |
| `NUM_RECENT_MONTHS`        | `1`                                            | Número de meses anteriores a verificar além do mês mais atual                                   |
| `TIME_CHECK_INTERVAL`      | `3600`                                         | Intervalo (em segundos) entre verificações. Ignora se a última estiver dentro do tempo          |
| `SETTINGS_FILE_PATH`       | Definido automaticamente                       | Caminho onde o `settings.json` será criado/atualizado                                           |
| `DEFAULT_DOWNLOAD_PATH`    | `~/Downloads/DadosCNPJ`                        | Caminho padrão para salvar os arquivos baixados                                                 |
| `DEFAULT_RFB_URL`          | [Link oficial](https://arquivos.receitafederal.gov.br/dados/cnpj/dados_abertos_cnpj/)  | URL padrão para acessar os arquivos da Receita Federal                                          |

---

### `DEFAULT_SETTINGS` gerado automaticamente

```json
{
  "download_path": DEFAULT_DOWNLOAD_PATH,
  "rfb_last_check": "",
  "rfb_url": DEFAULT_RFB_URL,
  "rfb_available": {}
}
```

> Os campos `download_path` e `rfb_url` podem ser alterados diretamente pela interface gráfica do app.

---

## Interface

### Tela inicial 
<img src="https://i.ibb.co/5hp3PwD0/Captura-de-tela-2025-04-11-144300.png" alt="Tela Geral" width="600"/>

- ✅ Baixado
- ⚠️ Parcialmente baixado
- ❌ Pendente

### Acompanhamento dos downloads

<img src="https://github.com/user-attachments/assets/64f1b319-d888-4332-88ae-6c485fb19866" alt="Downloads" width="300"/>

- 🔄 Retomar downloads que falharam
- 🧹 Limpar a lista (falhas, cancelados e concluídos)

### Configurações
<img src="https://i.ibb.co/hQpPCvS/Captura-de-tela-2025-04-11-145614.png" alt="Configurações" width="200"/>

---

## Estrutura dos Arquivos

```
DownloadCNPJ/
├── main.py               # Ponto de entrada (NiceGUI)
├── settings.py           # Configurações (caminho, parâmetros)
├── interface.py          # GUI da aplicação
├── folder_picker.py      # Seleção do caminho dos downloads
├── data_rfb.py           # Obtém os dados no portal da Receita Federal
├── data_download.py      # Gerenciador dos downloads
├── logs.py               # Geração de logs (em produção)
└── requirements.txt      # Dependências
```

---

## Melhorias e contribuições

A versão atual está funcional e estável na tarefa principal de auxiliar no download e manutenção dos arquivos.  
Melhorias na interface e performance estão planejadas para versões futuras, mas não são a prioridade no momento.

Contribuições são muito bem-vindas!  

---

## 📄 Licença

Distribuído sob a licença [MIT](LICENSE).
