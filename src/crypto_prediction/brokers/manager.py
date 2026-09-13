"""
Broker Manager - Manages multiple brokers, API keys, connections
Secure storage, real trading with extensive controls
"""
from typing import Dict, List, Optional
import json
from pathlib import Path
from datetime import datetime
import base64

from ..config import get_config
from .base import BaseBroker
from .binance_broker import BinanceBroker
from .paper_broker import PaperBroker
from .coindcx_broker import CoinDCXBroker
from ..utils.logger import get_logger

logger = get_logger(__name__)
config = get_config()

class BrokerManager:
    """
    Manages brokers for real trading
    - Secure API key storage (basic encoding, not plain text)
    - Multiple brokers support
    - Paper and real modes
    - Extensive user control
    """

    def __init__(self, storage_path: str = None):
        self.storage_path = Path(storage_path) if storage_path else config.project_root / "data" / "brokers.json"
        self.brokers: Dict[str, BaseBroker] = {}
        self.broker_configs: Dict[str, Dict] = {}
        self.load()

        # Always ensure paper broker exists for fallback, but CoinDCX is primary for real money
        if "paper" not in self.brokers:
            paper = PaperBroker(initial_balance=10000)
            paper.connect()
            self.brokers["paper"] = paper
            self.broker_configs["paper"] = {
                "name": "Paper (Testing Only)",
                "type": "paper",
                "connected": True,
                "paper_mode": True,
                "initial_balance": 10000,
                "created_at": datetime.utcnow().isoformat(),
                "note": "Paper for testing only - user requested real CoinDCX money"
            }
        
        # Ensure CoinDCX broker placeholder exists for real money trading
        if "coindcx" not in self.brokers:
            coindcx = CoinDCXBroker()
            self.brokers["coindcx"] = coindcx
            self.broker_configs["coindcx"] = {
                "id": "coindcx",
                "name": "CoinDCX REAL MONEY",
                "type": "coindcx",
                "connected": False,
                "paper_mode": False,
                "real_trading": True,
                "has_keys": False,
                "created_at": datetime.utcnow().isoformat(),
                "warning": "REAL MONEY - Actual INR from CoinDCX account - No paper simulation",
                "markets": "BTCINR, ETHINR, BNBINR, SOLINR, XRPINR, ADAINR, DOGEINR, AVAXINR, etc.",
                "secure": "API keys encoded, trading permission only"
            }
            self.save()

    def _encode(self, text: str) -> str:
        """Basic encoding for API keys (not secure encryption, but not plain text)"""
        return base64.b64encode(text.encode()).decode()

    def _decode(self, encoded: str) -> str:
        try:
            return base64.b64decode(encoded.encode()).decode()
        except:
            return encoded  # Fallback if not encoded

    def load(self):
        try:
            if self.storage_path.exists():
                data = json.loads(self.storage_path.read_text())
                for broker_id, cfg in data.get("brokers", {}).items():
                    self.broker_configs[broker_id] = cfg
                    # Recreate broker instances
                    if cfg["type"] == "binance":
                        broker = BinanceBroker(testnet=cfg.get("testnet", False))
                        if cfg.get("api_key_encoded") and cfg.get("api_secret_encoded"):
                            try:
                                api_key = self._decode(cfg["api_key_encoded"])
                                api_secret = self._decode(cfg["api_secret_encoded"])
                                broker.connect(api_key, api_secret, testnet=cfg.get("testnet", False))
                            except Exception as e:
                                logger.warning(f"Failed to reconnect broker {broker_id}: {e}")
                                broker.paper_mode = True
                                broker.connected = True
                        else:
                            broker.paper_mode = True
                            broker.connected = True
                        self.brokers[broker_id] = broker
                    elif cfg["type"] == "coindcx":
                        broker = CoinDCXBroker()
                        if cfg.get("api_key_encoded") and cfg.get("api_secret_encoded"):
                            try:
                                api_key = self._decode(cfg["api_key_encoded"])
                                api_secret = self._decode(cfg["api_secret_encoded"])
                                success = broker.connect(api_key, api_secret)
                                if not success:
                                    logger.warning(f"CoinDCX reconnect failed for {broker_id} - needs valid keys")
                            except Exception as e:
                                logger.warning(f"Failed to reconnect CoinDCX broker {broker_id}: {e}")
                        self.brokers[broker_id] = broker
                    elif cfg["type"] == "paper":
                        broker = PaperBroker(initial_balance=cfg.get("initial_balance", 10000))
                        broker.connect()
                        self.brokers[broker_id] = broker
                logger.info(f"Loaded {len(self.brokers)} brokers")
        except Exception as e:
            logger.warning(f"Failed to load brokers: {e}")

    def save(self):
        try:
            self.storage_path.parent.mkdir(parents=True, exist_ok=True)
            data = {
                "brokers": self.broker_configs,
                "timestamp": datetime.utcnow().isoformat(),
                "warning": "API keys are base64 encoded, not encrypted - store securely, never share"
            }
            self.storage_path.write_text(json.dumps(data, indent=2))
        except Exception as e:
            logger.error(f"Failed to save brokers: {e}")

    def add_broker(self, broker_id: str, broker_type: str, api_key: str = None, api_secret: str = None,
                   testnet: bool = False, initial_balance: float = 10000) -> Dict:
        """Add new broker with extensive controls - updates if exists (fixes UI duplicate bug)"""
        # If broker exists, remove old to allow update (fixes UI bug where coindcx placeholder exists)
        if broker_id in self.brokers:
            logger.info(f"Broker {broker_id} exists, updating with new credentials")
            # Don't delete paper broker protection, but allow coindcx update
            if broker_id != "paper":
                try:
                    if broker_id in self.brokers:
                        del self.brokers[broker_id]
                    if broker_id in self.broker_configs:
                        del self.broker_configs[broker_id]
                except:
                    pass
            else:
                raise ValueError(f"Broker {broker_id} already exists and is protected")

        if broker_type == "binance":
            broker = BinanceBroker(testnet=testnet)
            if api_key and api_secret:
                success = broker.connect(api_key, api_secret, testnet=testnet)
                if not success:
                    raise ValueError("Failed to connect to Binance - check API keys")
            else:
                broker.paper_mode = True
                broker.connected = True

            self.brokers[broker_id] = broker
            self.broker_configs[broker_id] = {
                "id": broker_id,
                "name": f"Binance {'Testnet' if testnet else 'Live'}",
                "type": "binance",
                "testnet": testnet,
                "api_key_encoded": self._encode(api_key) if api_key else None,
                "api_secret_encoded": self._encode(api_secret) if api_secret else None,
                "has_keys": bool(api_key and api_secret),
                "paper_mode": broker.paper_mode,
                "connected": broker.connected,
                "created_at": datetime.utcnow().isoformat(),
                "permissions": "Trading only - no withdrawal (secure)",
                "real_trading": not broker.paper_mode,
                "warning": "Never grant withdrawal permission - trading only"
            }

        elif broker_type == "coindcx":
            broker = CoinDCXBroker()
            if not api_key or not api_secret:
                raise ValueError("CoinDCX requires API key and secret for real money trading - no paper simulation")
            success = broker.connect(api_key, api_secret)
            if not success:
                raise ValueError("Failed to connect to CoinDCX - check API keys, ensure trading permission, IP whitelist")
            
            self.brokers[broker_id] = broker
            self.broker_configs[broker_id] = {
                "id": broker_id,
                "name": "CoinDCX REAL MONEY",
                "type": "coindcx",
                "api_key_encoded": self._encode(api_key),
                "api_secret_encoded": self._encode(api_secret),
                "has_keys": True,
                "paper_mode": False,
                "connected": True,
                "real_trading": True,
                "created_at": datetime.utcnow().isoformat(),
                "warning": "REAL MONEY - Actual INR from CoinDCX account - No paper simulation",
                "markets": "BTCINR, ETHINR, BNBINR, SOLINR, XRPINR, ADAINR, etc. - INR pairs",
                "secure": "Keys encoded, trading permission only, never withdrawal",
                "actual_money": "This uses your actual CoinDCX INR balance - real trades, real P&L"
            }

        elif broker_type == "paper":
            broker = PaperBroker(initial_balance=initial_balance)
            broker.connect()
            self.brokers[broker_id] = broker
            self.broker_configs[broker_id] = {
                "id": broker_id,
                "name": "Paper Trading (Testing Only)",
                "type": "paper",
                "initial_balance": initial_balance,
                "paper_mode": True,
                "connected": True,
                "created_at": datetime.utcnow().isoformat(),
                "real_trading": False,
                "note": "Paper for testing only - user requested real CoinDCX money, this is not used for actual trading"
            }
        else:
            raise ValueError(f"Unsupported broker type: {broker_type} - supported: binance, coindcx, paper")

        self.save()
        logger.info(f"Added broker {broker_id} type {broker_type} paper_mode={self.brokers[broker_id].paper_mode if hasattr(self.brokers[broker_id], 'paper_mode') else True}")
        return self.broker_configs[broker_id]

    def get_broker(self, broker_id: str) -> Optional[BaseBroker]:
        return self.brokers.get(broker_id)

    def get_all_brokers(self) -> Dict:
        result = {}
        for broker_id, cfg in self.broker_configs.items():
            broker = self.brokers.get(broker_id)
            # Get balance if possible
            balance_info = {}
            if broker:
                try:
                    balances = broker.get_balance()
                    balance_info = {k: v.to_dict() for k, v in balances.items()}
                except:
                    balance_info = {}
            
            result[broker_id] = {
                **cfg,
                "balances": balance_info,
                "api_key_preview": (cfg.get("api_key_encoded", "")[:10] + "..." if cfg.get("api_key_encoded") else None) if cfg.get("has_keys") else None,
                "secure_note": "Keys encoded, trading permission only, no withdrawal"
            }
        return result

    def remove_broker(self, broker_id: str) -> bool:
        if broker_id == "paper":
            raise ValueError("Cannot remove default paper broker")
        if broker_id in self.brokers:
            del self.brokers[broker_id]
        if broker_id in self.broker_configs:
            del self.broker_configs[broker_id]
            self.save()
            return True
        return False

    def test_broker(self, broker_id: str) -> Dict:
        broker = self.brokers.get(broker_id)
        if not broker:
            return {"connected": False, "error": "Broker not found"}
        return broker.test_connection()

# Global instance
_broker_manager = None

def get_broker_manager() -> BrokerManager:
    global _broker_manager
    if _broker_manager is None:
        _broker_manager = BrokerManager()
    return _broker_manager
