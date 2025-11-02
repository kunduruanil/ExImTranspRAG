"""
Component 1: Daily Data Ingestion Script
Runs daily as a cron job to fetch trade data from multiple sources
Author: AI Trade Intelligence System
"""

import os
import sys
import json
import logging
import requests
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import configparser
import time

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/data_ingestion.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class ConfigManager:
    """Manages configuration from config.ini file"""
    
    def __init__(self, config_path='config.ini'):
        self.config = configparser.ConfigParser()
        if not os.path.exists(config_path):
            raise FileNotFoundError(f"Configuration file not found: {config_path}")
        self.config.read(config_path)
        logger.info(f"Configuration loaded from {config_path}")
    
    def get(self, section: str, key: str, fallback: str = None) -> str:
        """Safely get configuration value"""
        try:
            return self.config.get(section, key)
        except (configparser.NoSectionError, configparser.NoOptionError) as e:
            if fallback is not None:
                logger.warning(f"Config key {section}.{key} not found, using fallback")
                return fallback
            logger.error(f"Required config key not found: {section}.{key}")
            raise

class HSCodeManager:
    """Manages HS codes from local file"""
    
    def __init__(self, hs_codes_file='hs_codes.txt'):
        self.hs_codes_file = hs_codes_file
    
    def load_hs_codes(self) -> List[str]:
        """Load HS codes from text file"""
        try:
            if not os.path.exists(self.hs_codes_file):
                logger.error(f"HS codes file not found: {self.hs_codes_file}")
                return []
            
            with open(self.hs_codes_file, 'r') as f:
                # Read lines, strip whitespace, filter empty lines and comments
                codes = [line.strip() for line in f 
                        if line.strip() and not line.strip().startswith('#')]
            
            # Validate HS codes (should be 6 digits)
            valid_codes = []
            for code in codes:
                if len(code) == 6 and code.isdigit():
                    valid_codes.append(code)
                else:
                    logger.warning(f"Invalid HS code format: {code}")
            
            logger.info(f"Loaded {len(valid_codes)} valid HS codes")
            return valid_codes
            
        except Exception as e:
            logger.error(f"Error loading HS codes: {str(e)}")
            return []

class ComtradeAPIClient:
    """Client for UN Comtrade API"""
    
    def __init__(self, config: ConfigManager):
        self.base_url = "https://comtradeapi.un.org/data/v1/get"
        self.api_key = config.get('COMTRADE', 'api_key', fallback=None)
        self.rate_limit_delay = 1.0  # seconds between requests
        
    def fetch_monthly_stats(self, hs_code: str, reporter_code: str = 'all') -> Optional[List[Dict]]:
        """
        Fetch latest monthly statistics for an HS code
        
        Args:
            hs_code: 6-digit HS code
            reporter_code: Country code or 'all'
        
        Returns:
            List of trade statistics records
        """
        try:
            # Calculate date range (last 3 months to ensure we get latest available data)
            end_date = datetime.now()
            start_date = end_date - timedelta(days=90)
            
            params = {
                'subscription-key': self.api_key,
                'typeCode': 'C',  # Commodities
                'freqCode': 'M',  # Monthly
                'clCode': 'HS',  # HS Classification
                'period': f"{start_date.strftime('%Y%m')},{end_date.strftime('%Y%m')}",
                'reporterCode': reporter_code,
                'cmdCode': hs_code,
                'flowCode': 'M',  # Imports
                'partnerCode': 'all',
                'partner2Code': 0,
            }
            
            logger.info(f"Fetching Comtrade data for HS code {hs_code}")
            response = requests.get(self.base_url, params=params, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                if 'data' in data and data['data']:
                    logger.info(f"Retrieved {len(data['data'])} records for HS {hs_code}")
                    time.sleep(self.rate_limit_delay)
                    return data['data']
                else:
                    logger.warning(f"No data returned for HS {hs_code}")
                    return []
            else:
                logger.error(f"Comtrade API error: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            logger.error(f"Error fetching Comtrade data for HS {hs_code}: {str(e)}")
            return None

class BLDataAPIClient:
    """
    Client for Bill of Lading (B/L) Data APIs
    Supports multiple providers: Trademo, Panjiva, ImportGenius
    """
    
    def __init__(self, config: ConfigManager):
        self.provider = config.get('BL_DATA', 'provider', fallback='trademo')
        self.api_key = config.get('BL_DATA', 'api_key')
        self.base_url = config.get('BL_DATA', 'base_url')
        self.rate_limit_delay = 0.5
        
    def fetch_shipments(self, hs_code: str, days_back: int = 1) -> Optional[List[Dict]]:
        """
        Fetch new shipment records from last N days
        
        Args:
            hs_code: 6-digit HS code
            days_back: Number of days to look back (default: 1 for daily cron)
        
        Returns:
            List of shipment records
        """
        try:
            start_date = (datetime.now() - timedelta(days=days_back)).strftime('%Y-%m-%d')
            end_date = datetime.now().strftime('%Y-%m-%d')
            
            # Generic structure - adapt based on actual API provider
            headers = {
                'Authorization': f'Bearer {self.api_key}',
                'Content-Type': 'application/json'
            }
            
            params = {
                'hs_code': hs_code,
                'start_date': start_date,
                'end_date': end_date,
                'limit': 1000  # Adjust based on API limits
            }
            
            logger.info(f"Fetching B/L data for HS code {hs_code} from {start_date} to {end_date}")
            response = requests.get(
                f"{self.base_url}/shipments",
                headers=headers,
                params=params,
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                # Handle different API response structures
                shipments = self._parse_provider_response(data)
                logger.info(f"Retrieved {len(shipments)} shipments for HS {hs_code}")
                time.sleep(self.rate_limit_delay)
                return shipments
            elif response.status_code == 401:
                logger.error("B/L API authentication failed - check API key")
                return None
            else:
                logger.error(f"B/L API error: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            logger.error(f"Error fetching B/L data for HS {hs_code}: {str(e)}")
            return None
    
    def _parse_provider_response(self, data: Dict) -> List[Dict]:
        """Parse response based on provider format"""
        if self.provider == 'trademo':
            return data.get('shipments', [])
        elif self.provider == 'panjiva':
            return data.get('records', [])
        elif self.provider == 'importgenius':
            return data.get('data', [])
        else:
            # Generic fallback
            return data.get('shipments', data.get('records', data.get('data', [])))

class DataIngestionPipeline:
    """Main pipeline orchestrator for daily data ingestion"""
    
    def __init__(self, config_path='config.ini'):
        self.config = ConfigManager(config_path)
        self.hs_manager = HSCodeManager()
        self.comtrade_client = ComtradeAPIClient(self.config)
        self.bl_client = BLDataAPIClient(self.config)
        
        # Create output directory for raw data
        self.output_dir = 'data/raw'
        os.makedirs(self.output_dir, exist_ok=True)
        os.makedirs('logs', exist_ok=True)
        
    def run(self):
        """Execute the full daily ingestion pipeline"""
        logger.info("=" * 80)
        logger.info("Starting Daily Data Ingestion Pipeline")
        logger.info("=" * 80)
        
        # Load HS codes
        hs_codes = self.hs_manager.load_hs_codes()
        if not hs_codes:
            logger.error("No HS codes loaded. Exiting.")
            return
        
        # Initialize counters
        total_comtrade_records = 0
        total_bl_records = 0
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # Process each HS code
        for idx, hs_code in enumerate(hs_codes, 1):
            logger.info(f"\nProcessing HS Code {idx}/{len(hs_codes)}: {hs_code}")
            
            # Fetch Comtrade data
            comtrade_data = self.comtrade_client.fetch_monthly_stats(hs_code)
            if comtrade_data:
                self._save_raw_data(comtrade_data, f'comtrade_{hs_code}_{timestamp}.json')
                total_comtrade_records += len(comtrade_data)
            
            # Fetch B/L data
            bl_data = self.bl_client.fetch_shipments(hs_code)
            if bl_data:
                self._save_raw_data(bl_data, f'bl_{hs_code}_{timestamp}.json')
                total_bl_records += len(bl_data)
        
        # Summary
        logger.info("\n" + "=" * 80)
        logger.info("Daily Ingestion Pipeline Complete")
        logger.info(f"Total HS Codes Processed: {len(hs_codes)}")
        logger.info(f"Total Comtrade Records: {total_comtrade_records}")
        logger.info(f"Total B/L Records: {total_bl_records}")
        logger.info("=" * 80)
    
    def _save_raw_data(self, data: List[Dict], filename: str):
        """Save raw data to JSON file"""
        try:
            filepath = os.path.join(self.output_dir, filename)
            with open(filepath, 'w') as f:
                json.dump(data, f, indent=2)
            logger.debug(f"Saved raw data to {filepath}")
        except Exception as e:
            logger.error(f"Error saving raw data to {filename}: {str(e)}")

def main():
    """Main entry point for cron job"""
    try:
        pipeline = DataIngestionPipeline()
        pipeline.run()
    except Exception as e:
        logger.critical(f"Pipeline failed with error: {str(e)}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()
