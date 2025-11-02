# Trade Intelligence RAG Platform - Setup Guide

## 🚀 Quick Start

### 1. Prerequisites

- Python 3.9 or higher
- pip package manager
- Access to UN Comtrade API
- Bill of Lading data provider API key (Trademo/Panjiva/ImportGenius)
- OpenAI API key
- Pinecone account (or alternative vector DB)

### 2. Installation

```bash
# Clone or download the project
cd trade-intelligence-rag

# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Linux/Mac:
source venv/bin/activate
# On Windows:
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Configuration

```bash
# Copy the configuration template
cp config.ini.template config.ini

# Edit config.ini with your actual API keys
nano config.ini  # or use your preferred editor
```

**Required Configuration:**
- `[COMTRADE]`: UN Comtrade API key
- `[BL_DATA]`: Your B/L data provider credentials
- `[EMBEDDINGS]`: OpenAI API key (or configure Hugging Face)
- `[VECTOR_DB]`: Pinecone API key and index name
- `[LLM]`: OpenAI API key (usually same as embeddings)
- `[ALERTS]`: Email and/or Slack notification settings

### 4. Setup HS Codes

Create a file `hs_codes.txt` with your tracked HS codes (one per line):

```
# HS Codes to Track (6-digit codes)
851712
950300
840999
# Add more codes...
```

### 5. Create Directory Structure

```bash
mkdir -p data/raw data/processed logs
```

## 📋 Component-by-Component Setup

### Component 1: Data Ingestion (Cron Job)

**Test manually first:**
```bash
python component1_data_ingestion.py
```

**Setup daily cron job:**
```bash
# Edit crontab
crontab -e

# Add this line to run daily at 2 AM
0 2 * * * /path/to/venv/bin/python /path/to/component1_data_ingestion.py
```

**Expected Output:**
- Raw data files in `data/raw/`
- Logs in `logs/data_ingestion.log`

### Component 2: ETL & Vectorization

**Test manually:**
```bash
python component2_etl_vectorization.py
```

**Setup to run after ingestion:**
```bash
# Add to crontab (runs at 3 AM, after ingestion)
0 3 * * * /path/to/venv/bin/python /path/to/component2_etl_vectorization.py
```

**Expected Output:**
- Processed files moved to `data/processed/`
- Vectors stored in Pinecone
- Logs in `logs/etl_vectorization.log`

### Component 3: RAG Query Interface

**Interactive CLI Mode:**
```bash
python component3_rag_query.py --interactive
```

**Programmatic Usage:**
```python
from component3_rag_query import TradeIntelligenceRAG

rag = TradeIntelligenceRAG()
answer = rag.ask_complex_question("Who are the top buyers for HS code 851712?")
print(answer)
```

### Component 4: Automated Monitoring

**Configure Alert Rules:**

Edit `alert_rules.json` or modify the default rules in the code:

```json
[
  {
    "rule_id": "new_competitor_suppliers",
    "name": "New Suppliers to Competitors",
    "query": "Have any new suppliers shipped to MyCompetitor LLC in the last 24 hours?",
    "trigger_condition": "data_found",
    "keywords": [],
    "enabled": true,
    "priority": "high"
  }
]
```

**Test manually:**
```bash
python component4_monitoring_alerts.py
```

**Setup monitoring cron job:**
```bash
# Run every 6 hours
0 */6 * * * /path/to/venv/bin/python /path/to/component4_monitoring_alerts.py

# Or run hourly for critical monitoring
0 * * * * /path/to/venv/bin/python /path/to/component4_monitoring_alerts.py
```

## 🔧 Advanced Configuration

### Using Hugging Face Instead of OpenAI

```ini
[EMBEDDINGS]
provider = huggingface
hf_model = sentence-transformers/all-MiniLM-L6-v2
```

**Benefits:** Free, runs locally, no API costs
**Drawbacks:** Slower, requires GPU for optimal performance

### Using Alternative Vector Databases

**Weaviate:**
```ini
[VECTOR_DB]
provider = weaviate
weaviate_url = http://localhost:8080
```

**Milvus:**
```ini
[VECTOR_DB]
provider = milvus
milvus_host = localhost
milvus_port = 19530
```

### Email Configuration for Gmail

1. Enable 2-Factor Authentication in your Google account
2. Generate an App Password: https://myaccount.google.com/apppasswords
3. Use the app password in `config.ini`:

```ini
[ALERTS]
smtp_server = smtp.gmail.com
smtp_port = 587
smtp_user = your-email@gmail.com
smtp_password = your-16-char-app-password
```

### Slack Webhook Setup

1. Go to https://api.slack.com/apps
2. Create a new app
3. Enable Incoming Webhooks
4. Add webhook to your workspace
5. Copy the webhook URL to `config.ini`

## 🎯 Example Queries

Here are example queries you can ask the RAG system:

### Market Intelligence
- "Who are the top 5 importers of HS code 851712 in Germany?"
- "What is the average monthly import value for HS code 950300?"
- "Show me import trends for electronics (HS 8517) over the last 3 months"

### Competitive Intelligence
- "List all shipments from 'Supplier Inc.' to any buyers in Europe"
- "Show me all new buyers for HS code 950300 in the last month"
- "Have any of my competitors received shipments from new suppliers?"

### Supply Chain Monitoring
- "Has import volume from China decreased this month?"
- "Show me all shipments delayed at port of Los Angeles"
- "List suppliers that have started shipping new HS codes"

### Risk & Compliance
- "Are there any unusual shipment patterns for HS code 851712?"
- "Show me all shipments from sanctioned countries"
- "List any suppliers with significant volume changes (>20%)"

## 🔍 Troubleshooting

### Issue: No data returned from Comtrade API

**Solution:**
- Check API key is valid
- Verify HS codes are 6-digit format
- Check rate limits (1 request per second)
- Ensure date ranges are valid

### Issue: Vector insertion fails

**Solution:**
- Verify Pinecone index exists
- Check embedding dimensions match index
- Ensure API key has write permissions
- Check Pinecone quota limits

### Issue: Alerts not sending

**Solution:**
- Test email/Slack credentials manually
- Check firewall settings for SMTP
- Verify webhook URLs are correct
- Review alert trigger conditions

### Issue: Slow query performance

**Solution:**
- Reduce `top_k` parameter (default: 10)
- Add metadata filters to narrow search
- Consider using faster embedding model
- Optimize Pinecone index settings

## 📊 Monitoring & Maintenance

### Check System Health

```bash
# View recent logs
tail -f logs/data_ingestion.log
tail -f logs/etl_vectorization.log
tail -f logs/rag_query.log
tail -f logs/monitoring_alerts.log

# Check vector database stats
python -c "from component2_etl_vectorization import VectorDBManager; import configparser; config = configparser.ConfigParser(); config.read('config.ini'); vdb = VectorDBManager(config, 1536); print(vdb.index.describe_index_stats())"
```

### View Alert History

```bash
# View recent alerts
cat data/alert_history.json | jq '.[-10:]'
```

### Backup Strategy

```bash
# Backup configuration and rules
tar -czf backup_$(date +%Y%m%d).tar.gz config.ini alert_rules.json hs_codes.txt

# Backup processed data
tar -czf data_backup_$(date +%Y%m%d).tar.gz data/processed/
```

## 🚨 Production Deployment Checklist

- [ ] All API keys configured in `config.ini`
- [ ] HS codes file populated with actual codes
- [ ] Tested data ingestion manually
- [ ] Verified vector database connection
- [ ] Tested RAG queries with sample questions
- [ ] Configured alert rules for business needs
- [ ] Set up cron jobs for automation
- [ ] Configured email/Slack notifications
- [ ] Tested alert delivery
- [ ] Set up log rotation
- [ ] Documented custom alert rules
- [ ] Created backup strategy
- [ ] Set up monitoring dashboards (optional)

## 📞 Support

For issues or questions:
1. Check logs in `logs/` directory
2. Review configuration in `config.ini`
3. Test components individually
4. Check API provider documentation

## 🔄 Updates and Maintenance

### Regular Tasks
- **Daily**: Monitor logs for errors
- **Weekly**: Review alert triggers and adjust rules
- **Monthly**: Check vector database size and costs
- **Quarterly**: Update HS codes list as needed

### Scaling Considerations
- Pinecone free tier: 100K vectors
- Consider upgrading for >1000 HS codes
- Use Hugging Face embeddings to reduce API costs
- Implement data retention policies for old records
