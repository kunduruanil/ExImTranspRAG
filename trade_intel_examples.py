# Example Usage Scripts and Sample Files

"""
example_hs_codes.txt
-------------------
# Trade Intelligence Platform - HS Codes to Track
# Add one 6-digit HS code per line
# Lines starting with # are comments

# Electronics
851712
851770
854232

# Toys and Games
950300
950490

# Medical Equipment
901890
902780

# Automotive Parts
840999
870899

# Machinery
842490
847989
"""

"""
example_alert_rules.json
------------------------
"""
EXAMPLE_ALERT_RULES = [
    {
        "rule_id": "competitor_new_suppliers",
        "name": "Competitor New Suppliers Alert",
        "query": "Have any of these companies received shipments from new suppliers in the last 24 hours: CompetitorA Corp, CompetitorB LLC, CompetitorC Inc?",
        "trigger_condition": "data_found",
        "keywords": [],
        "enabled": True,
        "priority": "high"
    },
    {
        "rule_id": "volume_spike",
        "name": "Import Volume Spike Detection",
        "query": "Have import volumes for any of our tracked HS codes increased by more than 50% this week compared to last week?",
        "trigger_condition": "keyword_match",
        "keywords": ["yes", "increased", "spike", "surge"],
        "enabled": True,
        "priority": "medium"
    },
    {
        "rule_id": "new_market_entrants",
        "name": "New Market Entrants",
        "query": "List any new companies that have started importing HS codes 851712, 950300, or 840999 in the last 7 days.",
        "trigger_condition": "data_found",
        "keywords": [],
        "enabled": True,
        "priority": "medium"
    },
    {
        "rule_id": "supply_chain_disruption",
        "name": "Supply Chain Disruption Alert",
        "query": "Are there any shipment delays or disruptions for our top 5 suppliers in the last 48 hours?",
        "trigger_condition": "keyword_match",
        "keywords": ["delay", "disruption", "issue", "problem"],
        "enabled": True,
        "priority": "critical"
    },
    {
        "rule_id": "price_anomaly",
        "name": "Price Anomaly Detection",
        "query": "Have there been any unusual price changes (>30% increase or decrease) for tracked products this month?",
        "trigger_condition": "keyword_match",
        "keywords": ["yes", "unusual", "anomaly", "significant"],
        "enabled": True,
        "priority": "high"
    }
]

"""
Example 1: Basic Query Script
"""
def example_basic_query():
    """Example of basic RAG query"""
    from component3_rag_query import TradeIntelligenceRAG
    
    rag = TradeIntelligenceRAG()
    
    questions = [
        "Who are the top 3 importers of HS code 851712?",
        "What is the trend in import volumes for electronics?",
        "Show me recent shipments from China to Germany."
    ]
    
    for question in questions:
        print(f"\n{'='*80}")
        print(f"Question: {question}")
        print(f"{'='*80}")
        
        answer = rag.ask_complex_question(question)
        print(f"\nAnswer: {answer}\n")

"""
Example 2: Advanced Query with Filters
"""
def example_filtered_query():
    """Example of query with metadata filters"""
    from component3_rag_query import TradeIntelligenceRAG
    
    rag = TradeIntelligenceRAG()
    
    # Query with filters
    result = rag.query_with_filters(
        question="Show me all shipments from this supplier",
        filters={
            "source": "bill_of_lading",
            "supplier": "Supplier Inc.",
            "hs_code": "851712"
        },
        top_k=5
    )
    
    print(f"\nFiltered Query Results:")
    print(f"Answer: {result['answer']}")
    print(f"\nFound {result['num_sources']} matching shipments")
    
    for i, source in enumerate(result['sources'], 1):
        print(f"\n--- Source {i} ---")
        print(f"Text: {source['text']}")
        print(f"Metadata: {source['metadata']}")

"""
Example 3: Batch Query Processing
"""
def example_batch_queries():
    """Process multiple queries efficiently"""
    from component3_rag_query import ProgrammaticQueryInterface
    
    interface = ProgrammaticQueryInterface()
    
    questions = [
        "What are the top importing countries for HS code 950300?",
        "List new buyers in Europe for tracked HS codes",
        "Show me supplier concentration risk for HS code 851712",
        "What is the average shipment size for electronics imports?"
    ]
    
    print("\nProcessing batch queries...")
    results = interface.execute_batch_queries(questions)
    
    for i, result in enumerate(results, 1):
        print(f"\n{'='*80}")
        print(f"Query {i}: {result['question']}")
        print(f"Answer: {result['answer']}")
        print(f"{'='*80}")

"""
Example 4: Custom Alert Rule Creation
"""
def example_create_custom_alert():
    """Create and add a custom alert rule"""
    from component4_monitoring_alerts import MonitoringSystem, AlertRule
    
    monitoring = MonitoringSystem()
    
    # Create custom rule
    custom_rule = AlertRule(
        rule_id='custom_market_opportunity',
        name='Market Opportunity Detection',
        query='Are there any new buyers in emerging markets (India, Vietnam, Poland) for our tracked HS codes in the last 7 days?',
        trigger_condition='data_found',
        priority='medium'
    )
    
    # Add rule
    monitoring.add_rule(custom_rule)
    print(f"Added custom alert rule: {custom_rule.name}")

"""
Example 5: Manual Alert Testing
"""
def example_test_alert():
    """Test a single alert rule manually"""
    from component4_monitoring_alerts import MonitoringSystem
    
    monitoring = MonitoringSystem()
    
    # Get specific rule
    rule = next((r for r in monitoring.rules if r.rule_id == 'new_market_entrants'), None)
    
    if rule:
        print(f"Testing rule: {rule.name}")
        
        result = monitoring.query_interface.execute_query(rule.query, return_sources=True)
        should_trigger = monitoring._check_trigger_condition(rule, result)
        
        print(f"\nQuery: {rule.query}")
        print(f"Answer: {result['answer']}")
        print(f"\nWould trigger alert: {should_trigger}")
        
        if should_trigger:
            print("\n⚠️  This rule would trigger an alert!")
        else:
            print("\n✓ No alert triggered")

"""
Example 6: Data Validation Script
"""
def example_validate_data():
    """Validate ingested data quality"""
    import json
    import glob
    
    raw_files = glob.glob('data/raw/*.json')
    
    print(f"\n{'='*80}")
    print("Data Validation Report")
    print(f"{'='*80}\n")
    
    for filepath in raw_files[:5]:  # Check first 5 files
        with open(filepath, 'r') as f:
            data = json.load(f)
        
        print(f"\nFile: {filepath}")
        print(f"Records: {len(data)}")
        
        if data:
            sample = data[0]
            print(f"Sample keys: {list(sample.keys())[:5]}")

"""
Example 7: Vector Database Statistics
"""
def example_vector_db_stats():
    """Get statistics from vector database"""
    from component2_etl_vectorization import VectorDBManager
    import configparser
    
    config = configparser.ConfigParser()
    config.read('config.ini')
    
    vdb = VectorDBManager(config, 1536)
    
    stats = vdb.index.describe_index_stats()
    
    print(f"\n{'='*80}")
    print("Vector Database Statistics")
    print(f"{'='*80}\n")
    print(f"Total vectors: {stats.total_vector_count}")
    print(f"Dimension: {stats.dimension}")
    print(f"Index fullness: {stats.index_fullness}")

"""
Example 8: Custom Data Formatter
"""
def example_custom_formatter():
    """Example of formatting custom data source"""
    from component2_etl_vectorization import TextChunkFormatter
    
    # Example custom data
    custom_record = {
        'date': '2025-10-15',
        'company': 'CustomCorp',
        'hs_code': '851712',
        'value_usd': 125000,
        'notes': 'First shipment of new product line'
    }
    
    # Create custom formatter
    text = (
        f"Custom Trade Event: On {custom_record['date']}, "
        f"{custom_record['company']} recorded a transaction "
        f"for HS code {custom_record['hs_code']} valued at "
        f"${custom_record['value_usd']:,}. {custom_record['notes']}"
    )
    
    metadata = {
        'source': 'custom',
        'date': custom_record['date'],
        'company': custom_record['company'],
        'hs_code': custom_record['hs_code'],
        'value_usd': custom_record['value_usd']
    }
    
    print(f"\nFormatted text: {text}")
    print(f"Metadata: {metadata}")

"""
Example 9: End-to-End Test Script
"""
def run_end_to_end_test():
    """Run complete system test"""
    print("\n" + "="*80)
    print("Running End-to-End System Test")
    print("="*80 + "\n")
    
    # Test 1: Configuration
    print("✓ Testing configuration...")
    import configparser
    config = configparser.ConfigParser()
    config.read('config.ini')
    assert config.has_section('EMBEDDINGS'), "Config missing EMBEDDINGS section"
    print("  Configuration OK")
    
    # Test 2: HS Codes
    print("\n✓ Testing HS codes file...")
    with open('hs_codes.txt', 'r') as f:
        codes = [line.strip() for line in f if line.strip() and not line.startswith('#')]
    assert len(codes) > 0, "No HS codes found"
    print(f"  Found {len(codes)} HS codes")
    
    # Test 3: RAG Query
    print("\n✓ Testing RAG query system...")
    from component3_rag_query import TradeIntelligenceRAG
    rag = TradeIntelligenceRAG()
    answer = rag.ask_complex_question("Test query")
    assert answer is not None, "RAG query failed"
    print("  RAG system OK")
    
    # Test 4: Monitoring System
    print("\n✓ Testing monitoring system...")
    from component4_monitoring_alerts import MonitoringSystem
    monitoring = MonitoringSystem()
    assert len(monitoring.rules) > 0, "No alert rules loaded"
    print(f"  Monitoring system OK ({len(monitoring.rules)} rules)")
    
    print("\n" + "="*80)
    print("✅ All system tests passed!")
    print("="*80 + "\n")

"""
Example 10: Generate Sample Data (for testing)
"""
def generate_sample_data():
    """Generate sample data files for testing"""
    import json
    from datetime import datetime, timedelta
    
    # Sample Comtrade data
    comtrade_sample = [
        {
            "period": "202310",
            "reporterDesc": "Germany",
            "partnerDesc": "China",
            "cmdCode": "851712",
            "cmdDesc": "Smartphones",
            "primaryValue": 50000000,
            "qty": 100000,
            "qtyUnitAbbr": "units",
            "flowDesc": "Import"
        }
    ]
    
    # Sample B/L data
    bl_sample = [
        {
            "shipment_date": (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d'),
            "buyer": "TechCorp Germany",
            "supplier": "Manufacturing Ltd China",
            "hs_code": "851712",
            "product_description": "Smartphone Model X",
            "quantity": 5000,
            "weight_kg": 2500,
            "origin_country": "China",
            "destination_country": "Germany",
            "port_of_loading": "Shanghai",
            "port_of_discharge": "Hamburg"
        }
    ]
    
    # Save sample files
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    with open(f'data/raw/comtrade_851712_{timestamp}_sample.json', 'w') as f:
        json.dump(comtrade_sample, f, indent=2)
    
    with open(f'data/raw/bl_851712_{timestamp}_sample.json', 'w') as f:
        json.dump(bl_sample, f, indent=2)
    
    print("Sample data files generated in data/raw/")

# Main execution
if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        example = sys.argv[1]
        
        examples = {
            'basic': example_basic_query,
            'filtered': example_filtered_query,
            'batch': example_batch_queries,
            'alert': example_create_custom_alert,
            'test_alert': example_test_alert,
            'validate': example_validate_data,
            'stats': example_vector_db_stats,
            'formatter': example_custom_formatter,
            'e2e': run_end_to_end_test,
            'sample': generate_sample_data
        }
        
        if example in examples:
            examples[example]()
        else:
            print(f"Available examples: {', '.join(examples.keys())}")
    else:
        print("Usage: python examples.py <example_name>")
        print("\nAvailable examples:")
        print("  basic      - Basic RAG queries")
        print("  filtered   - Filtered queries")
        print("  batch      - Batch processing")
        print("  alert      - Create custom alert")
        print("  test_alert - Test alert rule")
        print("  validate   - Validate data")
        print("  stats      - Vector DB stats")
        print("  formatter  - Custom formatter")
        print("  e2e        - End-to-end test")
        print("  sample     - Generate sample data")
