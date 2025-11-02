"""
Component 4: Automated Monitoring & Alert System
Runs critical queries on schedule and triggers alerts when conditions are met
"""

import os
import json
import logging
from datetime import datetime
from typing import List, Dict, Optional
import configparser
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# Slack integration
import requests

# Import RAG query interface
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from component3_rag_query import ProgrammaticQueryInterface

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/monitoring_alerts.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class AlertRule:
    """Represents a single monitoring rule/alarm"""
    
    def __init__(self, rule_id: str, name: str, query: str, 
                 trigger_condition: str = 'data_found',
                 keywords: List[str] = None,
                 enabled: bool = True,
                 priority: str = 'medium'):
        """
        Initialize alert rule
        
        Args:
            rule_id: Unique identifier for the rule
            name: Human-readable name
            query: Natural language query to execute
            trigger_condition: 'data_found', 'keyword_match', or 'always'
            keywords: List of keywords to check for (if trigger_condition='keyword_match')
            enabled: Whether rule is active
            priority: 'low', 'medium', 'high', or 'critical'
        """
        self.rule_id = rule_id
        self.name = name
        self.query = query
        self.trigger_condition = trigger_condition
        self.keywords = keywords or []
        self.enabled = enabled
        self.priority = priority
        self.last_triggered = None
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for serialization"""
        return {
            'rule_id': self.rule_id,
            'name': self.name,
            'query': self.query,
            'trigger_condition': self.trigger_condition,
            'keywords': self.keywords,
            'enabled': self.enabled,
            'priority': self.priority,
            'last_triggered': self.last_triggered
        }
    
    @classmethod
    def from_dict(cls, data: Dict):
        """Create from dictionary"""
        rule = cls(
            rule_id=data['rule_id'],
            name=data['name'],
            query=data['query'],
            trigger_condition=data.get('trigger_condition', 'data_found'),
            keywords=data.get('keywords', []),
            enabled=data.get('enabled', True),
            priority=data.get('priority', 'medium')
        )
        rule.last_triggered = data.get('last_triggered')
        return rule

class AlertNotifier:
    """Handles sending alerts via different channels"""
    
    def __init__(self, config: configparser.ConfigParser):
        self.config = config
        
        # Email configuration
        self.email_enabled = config.getboolean('ALERTS', 'email_enabled', fallback=False)
        if self.email_enabled:
            self.smtp_server = config.get('ALERTS', 'smtp_server')
            self.smtp_port = config.getint('ALERTS', 'smtp_port')
            self.smtp_user = config.get('ALERTS', 'smtp_user')
            self.smtp_password = config.get('ALERTS', 'smtp_password')
            self.from_email = config.get('ALERTS', 'from_email')
            self.to_emails = config.get('ALERTS', 'to_emails').split(',')
        
        # Slack configuration
        self.slack_enabled = config.getboolean('ALERTS', 'slack_enabled', fallback=False)
        if self.slack_enabled:
            self.slack_webhook_url = config.get('ALERTS', 'slack_webhook_url')
        
        logger.info(f"Alert notifier initialized (Email: {self.email_enabled}, Slack: {self.slack_enabled})")
    
    def send_alert(self, rule: AlertRule, query_result: Dict):
        """
        Send alert through configured channels
        
        Args:
            rule: Alert rule that triggered
            query_result: Result from RAG query
        """
        try:
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            # Prepare alert message
            subject = f"🚨 Trade Alert: {rule.name} [{rule.priority.upper()}]"
            
            message = f"""
Trade Intelligence Alert Triggered
{'=' * 80}

Rule: {rule.name}
Priority: {rule.priority.upper()}
Triggered: {timestamp}

Query: {rule.query}

{'=' * 80}
ANSWER:
{'=' * 80}
{query_result['answer']}

{'=' * 80}
Sources: {query_result['num_sources']} relevant documents found
{'=' * 80}

This is an automated alert from your Trade Intelligence Monitoring System.
            """
            
            # Send via email
            if self.email_enabled:
                self._send_email(subject, message)
            
            # Send via Slack
            if self.slack_enabled:
                self._send_slack(rule, query_result, timestamp)
            
            logger.info(f"Alert sent successfully for rule: {rule.name}")
            
        except Exception as e:
            logger.error(f"Error sending alert: {str(e)}")
    
    def _send_email(self, subject: str, body: str):
        """Send email alert"""
        try:
            msg = MIMEMultipart()
            msg['From'] = self.from_email
            msg['To'] = ', '.join(self.to_emails)
            msg['Subject'] = subject
            
            msg.attach(MIMEText(body, 'plain'))
            
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.smtp_user, self.smtp_password)
                server.send_message(msg)
            
            logger.info(f"Email alert sent to {len(self.to_emails)} recipients")
            
        except Exception as e:
            logger.error(f"Error sending email: {str(e)}")
    
    def _send_slack(self, rule: AlertRule, query_result: Dict, timestamp: str):
        """Send Slack alert"""
        try:
            # Map priority to color
            color_map = {
                'low': '#36a64f',      # green
                'medium': '#ff9900',   # orange
                'high': '#ff0000',     # red
                'critical': '#8b0000'  # dark red
            }
            
            color = color_map.get(rule.priority, '#ff9900')
            
            # Create Slack message with rich formatting
            payload = {
                "text": f"🚨 Trade Alert: {rule.name}",
                "attachments": [
                    {
                        "color": color,
                        "fields": [
                            {
                                "title": "Rule",
                                "value": rule.name,
                                "short": True
                            },
                            {
                                "title": "Priority",
                                "value": rule.priority.upper(),
                                "short": True
                            },
                            {
                                "title": "Query",
                                "value": rule.query,
                                "short": False
                            },
                            {
                                "title": "Answer",
                                "value": query_result['answer'][:500] + "..." if len(query_result['answer']) > 500 else query_result['answer'],
                                "short": False
                            },
                            {
                                "title": "Sources",
                                "value": f"{query_result['num_sources']} relevant documents",
                                "short": True
                            },
                            {
                                "title": "Timestamp",
                                "value": timestamp,
                                "short": True
                            }
                        ],
                        "footer": "Trade Intelligence Monitoring System",
                        "ts": int(datetime.now().timestamp())
                    }
                ]
            }
            
            response = requests.post(
                self.slack_webhook_url,
                json=payload,
                headers={'Content-Type': 'application/json'}
            )
            
            if response.status_code == 200:
                logger.info("Slack alert sent successfully")
            else:
                logger.error(f"Slack API error: {response.status_code} - {response.text}")
                
        except Exception as e:
            logger.error(f"Error sending Slack alert: {str(e)}")

class MonitoringSystem:
    """Main monitoring and alerting system"""
    
    def __init__(self, config_path='config.ini', rules_file='alert_rules.json'):
        """Initialize monitoring system"""
        self.config = configparser.ConfigParser()
        self.config.read(config_path)
        
        self.rules_file = rules_file
        self.rules: List[AlertRule] = []
        self.load_rules()
        
        self.query_interface = ProgrammaticQueryInterface()
        self.notifier = AlertNotifier(self.config)
        
        # Alert history
        self.alert_history_file = 'data/alert_history.json'
        os.makedirs('data', exist_ok=True)
        
        logger.info(f"Monitoring system initialized with {len(self.rules)} rules")
    
    def load_rules(self):
        """Load alert rules from JSON file"""
        try:
            if os.path.exists(self.rules_file):
                with open(self.rules_file, 'r') as f:
                    rules_data = json.load(f)
                
                self.rules = [AlertRule.from_dict(rule) for rule in rules_data]
                logger.info(f"Loaded {len(self.rules)} alert rules")
            else:
                # Create default rules if file doesn't exist
                self._create_default_rules()
                self.save_rules()
                
        except Exception as e:
            logger.error(f"Error loading rules: {str(e)}")
            self._create_default_rules()
    
    def save_rules(self):
        """Save alert rules to JSON file"""
        try:
            rules_data = [rule.to_dict() for rule in self.rules]
            with open(self.rules_file, 'w') as f:
                json.dump(rules_data, f, indent=2)
            logger.info("Alert rules saved")
        except Exception as e:
            logger.error(f"Error saving rules: {str(e)}")
    
    def _create_default_rules(self):
        """Create default monitoring rules"""
        self.rules = [
            AlertRule(
                rule_id='new_competitor_suppliers',
                name='New Suppliers to Competitors',
                query='Have any new suppliers shipped to MyCompetitor LLC in the last 24 hours?',
                trigger_condition='data_found',
                priority='high'
            ),
            AlertRule(
                rule_id='volume_drop',
                name='Main Supplier Volume Drop',
                query='Has the import volume from MyMainSupplier dropped by more than 20% this month compared to last month?',
                trigger_condition='keyword_match',
                keywords=['yes', 'dropped', 'decrease', 'declined'],
                priority='critical'
            ),
            AlertRule(
                rule_id='new_buyers_hs950300',
                name='New Buyers for HS 950300',
                query='List any new buyers for HS code 950300 in Poland in the last 7 days.',
                trigger_condition='data_found',
                priority='medium'
            ),
            AlertRule(
                rule_id='competitor_activity',
                name='Competitor Shipment Activity',
                query='Show all shipments received by any of my tracked competitors in the last 24 hours.',
                trigger_condition='data_found',
                priority='medium'
            ),
            AlertRule(
                rule_id='price_changes',
                name='Significant Price Changes',
                query='Have there been any significant changes (>15%) in average import values for tracked HS codes this month?',
                trigger_condition='keyword_match',
                keywords=['yes', 'increased', 'decreased', 'change'],
                priority='high'
            )
        ]
        logger.info("Created default alert rules")
    
    def add_rule(self, rule: AlertRule):
        """Add a new alert rule"""
        self.rules.append(rule)
        self.save_rules()
        logger.info(f"Added new rule: {rule.name}")
    
    def remove_rule(self, rule_id: str):
        """Remove an alert rule"""
        self.rules = [r for r in self.rules if r.rule_id != rule_id]
        self.save_rules()
        logger.info(f"Removed rule: {rule_id}")
    
    def run_monitoring_cycle(self):
        """Execute one monitoring cycle - check all rules"""
        logger.info("=" * 80)
        logger.info("Starting Monitoring Cycle")
        logger.info("=" * 80)
        
        alerts_triggered = 0
        
        for rule in self.rules:
            if not rule.enabled:
                logger.info(f"Skipping disabled rule: {rule.name}")
                continue
            
            logger.info(f"\nChecking rule: {rule.name}")
            logger.info(f"Query: {rule.query}")
            
            try:
                # Execute query
                result = self.query_interface.execute_query(rule.query, return_sources=False)
                
                # Check trigger condition
                should_alert = self._check_trigger_condition(rule, result)
                
                if should_alert:
                    logger.info(f"✓ Alert condition met for rule: {rule.name}")
                    
                    # Get full result with sources for alert
                    full_result = self.query_interface.execute_query(rule.query, return_sources=True)
                    
                    # Send alert
                    self.notifier.send_alert(rule, full_result)
                    
                    # Update rule
                    rule.last_triggered = datetime.now().isoformat()
                    
                    # Save to history
                    self._save_alert_history(rule, full_result)
                    
                    alerts_triggered += 1
                else:
                    logger.info(f"✗ No alert triggered for rule: {rule.name}")
                    
            except Exception as e:
                logger.error(f"Error checking rule {rule.name}: {str(e)}")
        
        # Save updated rules
        self.save_rules()
        
        logger.info("\n" + "=" * 80)
        logger.info(f"Monitoring Cycle Complete - {alerts_triggered} alerts triggered")
        logger.info("=" * 80)
    
    def _check_trigger_condition(self, rule: AlertRule, result: Dict) -> bool:
        """Check if alert should be triggered based on rule condition"""
        answer = result['answer'].lower()
        
        if rule.trigger_condition == 'always':
            return True
        
        elif rule.trigger_condition == 'data_found':
            # Check if answer indicates data was found
            positive_indicators = ['yes', 'found', 'detected', 'identified', 'new', 
                                  'shipment', 'buyer', 'supplier', 'increased', 'decreased']
            negative_indicators = ['no', 'none', 'not found', 'no data', 'no records', 
                                  'no shipments', 'no buyers', 'no suppliers']
            
            # If explicitly negative, don't trigger
            if any(neg in answer for neg in negative_indicators):
                return False
            
            # If has positive indicators or substantial content, trigger
            if any(pos in answer for pos in positive_indicators):
                return True
            
            # If answer is substantial (>150 chars), consider it data found
            return len(answer) > 150
        
        elif rule.trigger_condition == 'keyword_match':
            # Check for specific keywords
            return any(keyword.lower() in answer for keyword in rule.keywords)
        
        return False
    
    def _save_alert_history(self, rule: AlertRule, result: Dict):
        """Save triggered alert to history"""
        try:
            # Load existing history
            history = []
            if os.path.exists(self.alert_history_file):
                with open(self.alert_history_file, 'r') as f:
                    history = json.load(f)
            
            # Add new alert
            alert_record = {
                'timestamp': datetime.now().isoformat(),
                'rule_id': rule.rule_id,
                'rule_name': rule.name,
                'priority': rule.priority,
                'query': rule.query,
                'answer': result['answer'],
                'num_sources': result['num_sources']
            }
            history.append(alert_record)
            
            # Keep only last 1000 alerts
            if len(history) > 1000:
                history = history[-1000:]
            
            # Save
            with open(self.alert_history_file, 'w') as f:
                json.dump(history, f, indent=2)
                
        except Exception as e:
            logger.error(f"Error saving alert history: {str(e)}")

def main():
    """Main entry point for monitoring script (to be run as cron job)"""
    try:
        monitoring = MonitoringSystem()
        monitoring.run_monitoring_cycle()
    except Exception as e:
        logger.critical(f"Monitoring system failed: {str(e)}", exc_info=True)
        raise

if __name__ == "__main__":
    main()
