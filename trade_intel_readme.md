# 🌍 Trade Intelligence RAG Platform

> **Automated Trade Intelligence System with Natural Language Querying**  
> Transform trade data into actionable insights using RAG (Retrieval-Augmented Generation)

[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## 📋 Overview

This platform automatically ingests, processes, and monitors international trade data using a modern RAG architecture with vector databases. Instead of traditional SQL queries, you can ask questions in natural language like:

- *"Who are the top 3 new buyers for HS code 851712 in the last month?"*
- *"Show me all shipments from 'Supplier Inc.' to any of my competitors."*
- *"What is the average monthly import value for HS code 950300 in Germany?"*

## 🎯 Key Features

### 🔄 Automated Data Pipeline
- **Daily ingestion** from UN Comtrade API (macro statistics)
- **Real-time updates** from Bill of Lading providers (micro shipments)
- **Intelligent ETL** converts raw data into searchable "memory"
- **Vector embeddings** for semantic search capabilities

### 🤖 Natural Language Interface
- Ask questions in plain English
- Context-aware responses using GPT-4
- Cite sources automatically
- Filter by date, company, country, HS code

### 🚨 Automated Monitoring
- Set up "alarm queries" for critical events
- Automatic email and Slack notifications
- Customizable trigger conditions
- Alert history tracking

### 📊 Data Sources
1. **UN Comtrade** - Monthly trade statistics by country and HS code
2. **Bill of Lading APIs** - Shipment-level transaction data
   - Trademo
   - Panjiva
   - ImportGenius

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    TRADE INTELLIGENCE RAG                    │
└─────────────────────────────────────────────────────────────┘

┌──────────────┐  ┌──────────────┐
│  Comtrade    │  │  B/L APIs    │
│     API      │  │  (Daily)     │
└──────┬───────┘  └──────┬───────┘
       │                 │
       └────────┬────────┘
                │
                ▼
    ┌───────────────────────┐
    │  Component 1: Ingest  │
    │   (Daily Cron Job)    │
    └───────────┬───────────┘
                │
                ▼
    ┌───────────────────────┐
    │  Component 2: ETL     │
    │  • Format to text     │
    │  • Generate embeddings│
    │  • Store in Vector DB │
    └───────────┬───────────┘
                │
                ▼
        ┌───────────────┐
        │  Pinecone DB  │
        │  (Vectors)    │
        └───────┬───────┘
                │
    ┌───────────┴───────────┐
    │                       │
    ▼                       ▼
┌───────────────┐   ┌───────────────┐
│ Component 3:  │   │ Component 4:  │
│  RAG Query    │   │  Monitoring   │
│  Interface    │   │  & Alerts     │
└───────────────┘   └───────────────┘
```

## 🚀 Quick Start

### Prerequisites
```bash
# Required
- Python 3.9+
- UN Comtrade API key
- Bill of Lading API key (Trademo/Panjiva/ImportGenius)
- OpenAI API key
- Pinecone account

# Optional
- Slack workspace (for alerts)
- Email account (for alerts)
```

### Installation

```bash
# 1. Clone repository
git clone https://github.com/yourcompany/trade-intelligence-rag.git
cd trade-intelligence-rag

# 2. Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure
cp config.ini.template config.ini
# Edit config.ini with your API keys

# 5. Setup HS codes
echo "851712" >> hs_codes.txt
echo "950300" >> hs_codes.txt

# 6. Create directories
mkdir -p data/raw data/processed logs

# 7. Test the system
python examples.py e2e
```

### First Run

```bash
# 1. Ingest sample data
python component1_data_ingestion.py

# 2. Process and vectorize
python component2_etl_vectorization.py

# 3. Try interactive queries
python component3_rag_query.py --interactive

# 4. Test monitoring
python component4_monitoring_alerts.py
```

## 📚 Documentation

- **[Setup Guide](SETUP.md)** - Detailed installation and configuration
- **[API Documentation](docs/API.md)** - Programmatic usage
- **[Alert Configuration](docs/ALERTS.md)** - Setting up monitoring rules
- **[Troubleshooting](docs/TROUBLESHOOTING.md)** - Common issues and solutions

## 💡 Usage Examples

### Interactive Queries

```bash
python component3_rag_query.py --interactive
```

```
🔍 Your Question: Who are the top buyers for HS code 851712 in Germany?

📊 ANSWER:
Based on recent shipment data, the top buyers for HS code 851712 
(smartphones) in Germany are:

1. TechCorp GmbH - 15,000 units imported in the last month
2. Electronics AG - 12,500 units
3. Mobile Solutions Ltd - 8,300 units

These companies account for 70% of total imports in this category.
```

### Programmatic Usage

```python
from component3_rag_query import TradeIntelligenceRAG

rag = TradeIntelligenceRAG()

# Simple question
answer = rag.ask_complex_question(
    "What is the trend in electronics imports from China?"
)
print(answer)

# Query with filters
result = rag.query_with_filters(
    question="Show me shipments from this supplier",
    filters={
        "supplier": "Supplier Inc.",
        "hs_code": "851712"
    }
)
```

### Setting Up Alerts

```python
from component4_monitoring_alerts import MonitoringSystem, AlertRule

monitoring = MonitoringSystem()

# Create custom alert
alert = AlertRule(
    rule_id='competitor_watch',
    name='Competitor Activity Monitor',
    query='Has MyCompetitor LLC received any shipments in the last 24 hours?',
    trigger_condition='data_found',
    priority='high'
)

monitoring.add_rule(alert)
```

## 🔧 Configuration

### Essential Configuration (`config.ini`)

```ini
[COMTRADE]
api_key = your_comtrade_key

[BL_DATA]
provider = trademo
api_key = your_bl_api_key
base_url = https://api.trademo.com/v1

[EMBEDDINGS]
provider = openai
openai_api_key = your_openai_key
openai_model = text-embedding-3-small

[VECTOR_DB]
provider = pinecone
pinecone_api_key = your_pinecone_key
pinecone_index_name = trade-intelligence

[ALERTS]
email_enabled = true
smtp_server = smtp.gmail.com
smtp_port = 587
smtp_user = your-email@gmail.com
smtp_password = your-app-password
```

### HS Codes to Track (`hs_codes.txt`)

```
# Electronics
851712
851770

# Toys
950300
950490

# Medical
901890
```

## 📅 Automation with Cron

```bash
# Edit crontab
crontab -e

# Add these lines:
# Daily data ingestion at 2 AM
0 2 * * * /path/to/venv/bin/python /path/to/component1_data_ingestion.py

# ETL processing at 3 AM
0 3 * * * /path/to/venv/bin/python /path/to/component2_etl_vectorization.py

# Monitoring checks every 6 hours
0 */6 * * * /path/to/venv/bin/python /path/to/component4_monitoring_alerts.py
```

## 🎓 Example Alert Rules

```json
{
  "rule_id": "new_suppliers",
  "name": "New Supplier Detection",
  "query": "Have any new suppliers started shipping HS code 851712 to Europe in the last week?",
  "trigger_condition": "data_found",
  "priority": "medium"
}
```

## 📊 System Requirements

### Minimum
- **CPU**: 2 cores
- **RAM**: 4 GB
- **Storage**: 10 GB
- **Python**: 3.9+

### Recommended
- **CPU**: 4+ cores
- **RAM**: 8+ GB
- **Storage**: 50+ GB (for data retention)
- **GPU**: Optional (for local embeddings)

## 💰 Cost Estimates

| Component | Free Tier | Paid Usage |
|-----------|-----------|------------|
| Pinecone | 100K vectors | $70/mo (1M vectors) |
| OpenAI Embeddings | - | ~$0.13 per 1M tokens |
| OpenAI GPT-4 | - | ~$10 per 1M tokens |
| UN Comtrade | 10K requests/mo | Free |
| B/L APIs | Varies | $500-2000/mo |

**Estimated monthly cost for 1000 HS codes**: $100-300

## 🔒 Security

- API keys stored in `config.ini` (never commit to git)
- Add `config.ini` to `.gitignore`
- Use environment variables in production
- Rotate API keys regularly
- Enable IP whitelisting where available

## 🤝 Contributing

We welcome contributions! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## 📄 License

This project is licensed under the MIT License - see [LICENSE](LICENSE) file for details.

## 🆘 Support

- **Documentation**: [docs/](docs/)
- **Issues**: [GitHub Issues](https://github.com/yourcompany/trade-intelligence-rag/issues)
- **Email**: support@yourcompany.com

## 🗺️ Roadmap

- [ ] Web dashboard interface
- [ ] Real-time data streaming
- [ ] Multi-language support
- [ ] Custom ML models for anomaly detection
- [ ] Mobile app
- [ ] Integration with ERP systems

## 🙏 Acknowledgments

- Built with [LlamaIndex](https://www.llamaindex.ai/)
- Vector search powered by [Pinecone](https://www.pinecone.io/)
- Embeddings from [OpenAI](https://openai.com/)
- Data from [UN Comtrade](https://comtradeapi.un.org/)

---

**Made with ❤️ for the global trade community**
