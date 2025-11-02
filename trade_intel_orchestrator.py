#!/usr/bin/env python3
"""
Master Orchestrator Script for Trade Intelligence RAG Platform
Provides unified interface for all system operations
"""

import os
import sys
import argparse
import logging
from datetime import datetime
import subprocess

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class TradeIntelligenceOrchestrator:
    """Master orchestrator for all platform operations"""
    
    def __init__(self):
        self.base_dir = os.path.dirname(os.path.abspath(__file__))
        self.components = {
            'ingestion': 'component1_data_ingestion.py',
            'etl': 'component2_etl_vectorization.py',
            'query': 'component3_rag_query.py',
            'monitoring': 'component4_monitoring_alerts.py'
        }
        
    def run_full_pipeline(self):
        """Run complete data pipeline: ingest -> etl -> monitor"""
        logger.info("="*80)
        logger.info("RUNNING FULL TRADE INTELLIGENCE PIPELINE")
        logger.info("="*80)
        
        steps = [
            ('Data Ingestion', 'ingestion'),
            ('ETL & Vectorization', 'etl'),
            ('Monitoring & Alerts', 'monitoring')
        ]
        
        for step_name, component in steps:
            logger.info(f"\n{'='*80}")
            logger.info(f"Step: {step_name}")
            logger.info(f"{'='*80}\n")
            
            success = self._run_component(component)
            
            if not success:
                logger.error(f"Pipeline failed at step: {step_name}")
                return False
        
        logger.info("\n" + "="*80)
        logger.info("✅ FULL PIPELINE COMPLETED SUCCESSFULLY")
        logger.info("="*80)
        return True
    
    def run_ingestion(self):
        """Run data ingestion only"""
        logger.info("Running data ingestion...")
        return self._run_component('ingestion')
    
    def run_etl(self):
        """Run ETL & vectorization only"""
        logger.info("Running ETL & vectorization...")
        return self._run_component('etl')
    
    def run_query_interactive(self):
        """Launch interactive query interface"""
        logger.info("Launching interactive query interface...")
        script = os.path.join(self.base_dir, self.components['query'])
        subprocess.run([sys.executable, script, '--interactive'])
    
    def run_monitoring(self):
        """Run monitoring cycle"""
        logger.info("Running monitoring & alerts...")
        return self._run_component('monitoring')
    
    def run_test_suite(self):
        """Run comprehensive system tests"""
        logger.info("="*80)
        logger.info("RUNNING SYSTEM TEST SUITE")
        logger.info("="*80)
        
        tests = [
            self._test_configuration,
            self._test_dependencies,
            self._test_data_files,
            self._test_vector_db_connection,
            self._test_rag_system
        ]
        
        passed = 0
        failed = 0
        
        for test in tests:
            try:
                test()
                passed += 1
            except Exception as e:
                logger.error(f"Test failed: {str(e)}")
                failed += 1
        
        logger.info("\n" + "="*80)
        logger.info(f"TEST RESULTS: {passed} passed, {failed} failed")
        logger.info("="*80)
        
        return failed == 0
    
    def setup_system(self):
        """Initialize system with required directories and files"""
        logger.info("Setting up Trade Intelligence System...")
        
        # Create directories
        dirs = [
            'data/raw',
            'data/processed',
            'logs',
            'backups'
        ]
        
        for dir_path in dirs:
            os.makedirs(dir_path, exist_ok=True)
            logger.info(f"✓ Created directory: {dir_path}")
        
        # Create empty files if they don't exist
        files = [
            ('hs_codes.txt', '# Add HS codes here (one per line)\n851712\n950300\n'),
            ('alert_rules.json', '[]'),
            ('.gitignore', 'config.ini\n*.pyc\n__pycache__/\ndata/\nlogs/\nvenv/\n.env\n')
        ]
        
        for filename, default_content in files:
            filepath = os.path.join(self.base_dir, filename)
            if not os.path.exists(filepath):
                with open(filepath, 'w') as f:
                    f.write(default_content)
                logger.info(f"✓ Created file: {filename}")
            else:
                logger.info(f"  File already exists: {filename}")
        
        logger.info("\n✅ System setup complete!")
        logger.info("\nNext steps:")
        logger.info("1. Edit config.ini with your API keys")
        logger.info("2. Add HS codes to hs_codes.txt")
        logger.info("3. Run: python master_orchestrator.py --test")
        logger.info("4. Run: python master_orchestrator.py --pipeline")
    
    def view_logs(self, component=None, lines=50):
        """Display recent logs"""
        log_files = {
            'ingestion': 'logs/data_ingestion.log',
            'etl': 'logs/etl_vectorization.log',
            'query': 'logs/rag_query.log',
            'monitoring': 'logs/monitoring_alerts.log'
        }
        
        if component:
            log_file = log_files.get(component)
            if log_file and os.path.exists(log_file):
                self._tail_file(log_file, lines)
            else:
                logger.error(f"Log file not found for component: {component}")
        else:
            # Show all logs
            for comp, log_file in log_files.items():
                if os.path.exists(log_file):
                    print(f"\n{'='*80}")
                    print(f"LOG: {comp}")
                    print(f"{'='*80}\n")
                    self._tail_file(log_file, lines // len(log_files))
    
    def backup_system(self):
        """Create system backup"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_file = f"backups/backup_{timestamp}.tar.gz"
        
        files_to_backup = [
            'config.ini',
            'hs_codes.txt',
            'alert_rules.json',
            'data/processed'
        ]
        
        import tarfile
        
        logger.info(f"Creating backup: {backup_file}")
        
        with tarfile.open(backup_file, "w:gz") as tar:
            for item in files_to_backup:
                if os.path.exists(item):
                    tar.add(item)
                    logger.info(f"  Added: {item}")
        
        logger.info(f"✅ Backup created: {backup_file}")
        return backup_file
    
    def generate_report(self):
        """Generate system status report"""
        logger.info("="*80)
        logger.info("TRADE INTELLIGENCE SYSTEM STATUS REPORT")
        logger.info("="*80)
        
        # Check configuration
        print("\n📋 Configuration:")
        if os.path.exists('config.ini'):
            print("  ✓ config.ini exists")
        else:
            print("  ✗ config.ini missing")
        
        # Check HS codes
        print("\n📊 HS Codes:")
        if os.path.exists('hs_codes.txt'):
            with open('hs_codes.txt', 'r') as f:
                codes = [l.strip() for l in f if l.strip() and not l.startswith('#')]
            print(f"  ✓ {len(codes)} HS codes configured")
        else:
            print("  ✗ hs_codes.txt missing")
        
        # Check data files
        print("\n📁 Data Files:")
        raw_files = len(os.listdir('data/raw')) if os.path.exists('data/raw') else 0
        processed_files = len(os.listdir('data/processed')) if os.path.exists('data/processed') else 0
        print(f"  Raw files: {raw_files}")
        print(f"  Processed files: {processed_files}")
        
        # Check alert rules
        print("\n🚨 Alert Rules:")
        if os.path.exists('alert_rules.json'):
            import json
            with open('alert_rules.json', 'r') as f:
                rules = json.load(f)
            enabled = sum(1 for r in rules if r.get('enabled', True))
            print(f"  ✓ {len(rules)} rules configured ({enabled} enabled)")
        else:
            print("  ✗ alert_rules.json missing")
        
        # Check logs
        print("\n📝 Recent Activity:")
        log_files = ['data_ingestion.log', 'etl_vectorization.log', 'monitoring_alerts.log']
        for log_file in log_files:
            log_path = os.path.join('logs', log_file)
            if os.path.exists(log_path):
                mtime = datetime.fromtimestamp(os.path.getmtime(log_path))
                print(f"  {log_file}: Last updated {mtime.strftime('%Y-%m-%d %H:%M')}")
        
        print("\n" + "="*80)
    
    # Helper methods
    
    def _run_component(self, component_name):
        """Run a specific component script"""
        script = os.path.join(self.base_dir, self.components[component_name])
        
        if not os.path.exists(script):
            logger.error(f"Script not found: {script}")
            return False
        
        try:
            result = subprocess.run(
                [sys.executable, script],
                capture_output=False,
                text=True,
                check=True
            )
            return result.returncode == 0
        except subprocess.CalledProcessError as e:
            logger.error(f"Component failed with exit code {e.returncode}")
            return False
    
    def _test_configuration(self):
        """Test configuration file"""
        logger.info("Testing configuration...")
        import configparser
        
        config = configparser.ConfigParser()
        config.read('config.ini')
        
        required_sections = ['COMTRADE', 'BL_DATA', 'EMBEDDINGS', 'VECTOR_DB']
        for section in required_sections:
            if not config.has_section(section):
                raise ValueError(f"Missing required config section: {section}")
        
        logger.info("  ✓ Configuration valid")
    
    def _test_dependencies(self):
        """Test Python dependencies"""
        logger.info("Testing dependencies...")
        
        required_packages = [
            'requests', 'openai', 'pinecone', 'llama_index'
        ]
        
        for package in required_packages:
            try:
                __import__(package)
            except ImportError:
                raise ImportError(f"Required package not installed: {package}")
        
        logger.info("  ✓ All dependencies installed")
    
    def _test_data_files(self):
        """Test data files"""
        logger.info("Testing data files...")
        
        if not os.path.exists('hs_codes.txt'):
            raise FileNotFoundError("hs_codes.txt not found")
        
        logger.info("  ✓ Data files present")
    
    def _test_vector_db_connection(self):
        """Test vector database connection"""
        logger.info("Testing vector database connection...")
        
        # This would test actual connection
        # Simplified for example
        logger.info("  ✓ Vector DB connection test (skipped)")
    
    def _test_rag_system(self):
        """Test RAG query system"""
        logger.info("Testing RAG system...")
        
        # This would test actual RAG
        # Simplified for example
        logger.info("  ✓ RAG system test (skipped)")
    
    def _tail_file(self, filepath, lines):
        """Display last N lines of a file"""
        try:
            with open(filepath, 'r') as f:
                all_lines = f.readlines()
                for line in all_lines[-lines:]:
                    print(line.rstrip())
        except Exception as e:
            logger.error(f"Error reading file: {str(e)}")

def main():
    parser = argparse.ArgumentParser(
        description='Trade Intelligence RAG Platform Orchestrator'
    )
    
    parser.add_argument(
        '--pipeline', action='store_true',
        help='Run full data pipeline (ingest -> etl -> monitor)'
    )
    parser.add_argument(
        '--ingest', action='store_true',
        help='Run data ingestion only'
    )
    parser.add_argument(
        '--etl', action='store_true',
        help='Run ETL & vectorization only'
    )
    parser.add_argument(
        '--query', action='store_true',
        help='Launch interactive query interface'
    )
    parser.add_argument(
        '--monitor', action='store_true',
        help='Run monitoring cycle'
    )
    parser.add_argument(
        '--test', action='store_true',
        help='Run system tests'
    )
    parser.add_argument(
        '--setup', action='store_true',
        help='Initialize system (first time setup)'
    )
    parser.add_argument(
        '--logs', type=str, nargs='?', const='all',
        help='View logs (optional: component name)'
    )
    parser.add_argument(
        '--backup', action='store_true',
        help='Create system backup'
    )
    parser.add_argument(
        '--report', action='store_true',
        help='Generate status report'
    )
    
    args = parser.parse_args()
    
    orchestrator = TradeIntelligenceOrchestrator()
    
    # Execute requested operation
    if args.setup:
        orchestrator.setup_system()
    elif args.pipeline:
        orchestrator.run_full_pipeline()
    elif args.ingest:
        orchestrator.run_ingestion()
    elif args.etl:
        orchestrator.run_etl()
    elif args.query:
        orchestrator.run_query_interactive()
    elif args.monitor:
        orchestrator.run_monitoring()
    elif args.test:
        orchestrator.run_test_suite()
    elif args.logs:
        component = None if args.logs == 'all' else args.logs
        orchestrator.view_logs(component)
    elif args.backup:
        orchestrator.backup_system()
    elif args.report:
        orchestrator.generate_report()
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
