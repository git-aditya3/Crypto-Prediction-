"""
Broker Manager - Manages multiple brokers, API keys, connections
Fixed: thread safety, decode fallback, avoid balance fetch for disconnected, CoinDCX integration
"""
from typing import Dict, List, Optional
import json
from pathlib import Path
from datetime import datetime
import base64
import threading

from ..config import get_config
from .base import BaseBroker
from .binance_broker import BinanceBroker
from .paper_broker import PaperBroker
from .coindcx_broker import CoinDCXBroker
from ..utils.logger import get_logger

logger = get_logger(__name__)
config = get_config()

class BrokerManager:
    def __init__(self, storage_path: str = None):
        self.storage_path = Path(storage_path) if storage_path else config.project_root / "data" / "brokers.json"
        self.brokers: Dict[str, BaseBroker] = {}
        self.broker_configs: Dict[str, Dict] = {}
        self._lock = threading.Lock()
        self.load()

        with self._lock:
            if "paper" not in self.brokers:
                paper = PaperBroker(initial_balance=10000)
                try:
                    paper.connect()
                except Exception as e:
                    logger.warning(f"Paper broker connect failed: {e}")
                self.brokers["paper"] = paper
                self.broker_configs["paper"] = {
                    "name": "Paper (Testing Only)",
                    "type": "paper",
                    "connected": True,
                    "paper_mode": True,
                    "initial_balance": 10000,
                    "created_at": datetime.utcnow().isoformat(),
                    "note": "Paper for testing only - real trading via CoinDCX"
                }

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
        try:
            self.save()
        except Exception as e:
            logger.debug(f"Initial save failed: {e}")

    def _encode(self, text: str) -> str:
        if not text:
            return ""
        try:
            return base64.b64encode(text.encode('utf-8')).decode('utf-8')
        except Exception:
            return text

    def _decode(self, encoded: str) -> str:
        if not encoded:
            return ""
        try:
            # Try base64 decode
            decoded = base64.b64decode(encoded.encode('utf-8')).decode('utf-8')
            # Validate decoded looks like key (not gibberish)
            if len(decoded) >= 8:
                return decoded
            return encoded
        except Exception:
            # If not base64, return as is (might be plain text from old version)
            return encoded

    def load(self):
        try:
            if self.storage_path.exists():
                data = json.loads(self.storage_path.read_text())
                brokers_data = data.get("brokers", {})
                if not isinstance(brokers_data, dict):
                    logger.warning("Brokers file invalid format")
                    return
                for broker_id, cfg in brokers_data.items():
                    if not isinstance(cfg, dict):
                        continue
                    if not isinstance(broker_id, str) or len(broker_id) > 50:
                        continue
                    self.broker_configs[broker_id] = cfg
                    try:
                        b_type = cfg.get("type","paper")
                        if b_type == "binance":
                            broker = BinanceBroker(testnet=cfg.get("testnet", False))
                            api_key_enc = cfg.get("api_key_encoded")
                            api_secret_enc = cfg.get("api_secret_encoded")
                            if api_key_enc and api_secret_enc:
                                try:
                                    api_key = self._decode(api_key_enc)
                                    api_secret = self._decode(api_secret_enc)
                                    if api_key and api_secret and len(api_key) > 8:
                                        success = broker.connect(api_key, api_secret, testnet=cfg.get("testnet", False))
                                        if not success:
                                            logger.warning(f"Binance reconnect failed {broker_id}, fallback to paper")
                                            broker.paper_mode = True
                                            broker.connected = True
                                except Exception as e:
                                    logger.warning(f"Failed to reconnect broker {broker_id}: {e}")
                                    broker.paper_mode = True
                                    broker.connected = True
                            else:
                                broker.paper_mode = True
                                broker.connected = True
                            with self._lock:
                                self.brokers[broker_id] = broker
                        elif b_type == "coindcx":
                            broker = CoinDCXBroker()
                            api_key_enc = cfg.get("api_key_encoded")
                            api_secret_enc = cfg.get("api_secret_encoded")
                            if api_key_enc and api_secret_enc:
                                try:
                                    api_key = self._decode(api_key_enc)
                                    api_secret = self._decode(api_secret_enc)
                                    if api_key and api_secret and len(api_key) > 8:
                                        success = broker.connect(api_key, api_secret)
                                        if not success:
                                            logger.warning(f"CoinDCX reconnect failed for {broker_id}")
                                except Exception as e:
                                    logger.warning(f"Failed to reconnect CoinDCX broker {broker_id}: {e}")
                            with self._lock:
                                self.brokers[broker_id] = broker
                        elif b_type == "paper":
                            try:
                                initial = float(cfg.get("initial_balance", 10000))
                            except (ValueError, TypeError):
                                initial = 10000
                            broker = PaperBroker(initial_balance=initial)
                            try:
                                broker.connect()
                            except Exception as e:
                                logger.warning(f"Paper broker connect failed {broker_id}: {e}")
                            with self._lock:
                                self.brokers[broker_id] = broker
                    except Exception as e:
                        logger.warning(f"Failed to load broker {broker_id}: {e}")
                        continue
                logger.info(f"Loaded {len(self.brokers)} brokers")
        except json.JSONDecodeError as e:
            logger.warning(f"Brokers file JSON invalid: {e}")
        except Exception as e:
            logger.warning(f"Failed to load brokers: {e}")

    def save(self):
        try:
            self.storage_path.parent.mkdir(parents=True, exist_ok=True)
            with self._lock:
                configs_copy = dict(self.broker_configs)
            data = {
                "brokers": configs_copy,
                "timestamp": datetime.utcnow().isoformat(),
                "warning": "API keys are base64 encoded, not encrypted - store securely, never share",
                "real_trading": "CoinDCX REAL MONEY - actual INR"
            }
            # Write atomically
            tmp_path = self.storage_path.with_suffix('.tmp')
            tmp_path.write_text(json.dumps(data, indent=2))
            tmp_path.replace(self.storage_path)
        except Exception as e:
            logger.error(f"Failed to save brokers: {e}")

    def add_broker(self, broker_id: str, broker_type: str, api_key: str = None, api_secret: str = None,
                   testnet: bool = False, initial_balance: float = 10000) -> Dict:
        if not broker_id or not isinstance(broker_id, str):
            raise ValueError("broker_id must be non-empty string")
        broker_id = broker_id.strip().lower()
        if len(broker_id) < 2 or len(broker_id) > 50:
            raise ValueError("broker_id must be 2-50 chars")
        if broker_id in ["", "null", "undefined"]:
            raise ValueError("Invalid broker_id")

        if broker_type not in ["binance", "coindcx", "paper"]:
            raise ValueError(f"Unsupported broker type: {broker_type}")

        with self._lock:
            if broker_id in self.brokers and broker_id == "paper":
                raise ValueError("Cannot overwrite default paper broker - use different id")

        # Remove existing if updating (except paper)
        if broker_id in self.brokers and broker_id != "paper":
            logger.info(f"Broker {broker_id} exists, updating")
            with self._lock:
                try:
                    if broker_id in self.brokers:
                        del self.brokers[broker_id]
                    if broker_id in self.broker_configs:
                        del self.broker_configs[broker_id]
                except Exception:
                    pass

        try:
            initial_balance = float(initial_balance)
            if initial_balance < 0 or initial_balance > 100_000_000:
                initial_balance = 10000
        except (ValueError, TypeError):
            initial_balance = 10000

        if broker_type == "binance":
            broker = BinanceBroker(testnet=bool(testnet))
            if api_key and api_secret:
                if len(api_key.strip()) < 8 or len(api_secret.strip()) < 8:
                    raise ValueError("API keys too short")
                success = broker.connect(api_key.strip(), api_secret.strip(), testnet=bool(testnet))
                if not success:
                    raise ValueError("Failed to connect to Binance - check API keys")
            else:
                broker.paper_mode = True
                broker.connected = True

            cfg = {
                "id": broker_id,
                "name": f"Binance {'Testnet' if testnet else 'Live'}",
                "type": "binance",
                "testnet": bool(testnet),
                "api_key_encoded": self._encode(api_key) if api_key else None,
                "api_secret_encoded": self._encode(api_secret) if api_secret else None,
                "has_keys": bool(api_key and api_secret),
                "paper_mode": getattr(broker, 'paper_mode', True),
                "connected": getattr(broker, 'connected', False),
                "created_at": datetime.utcnow().isoformat(),
                "permissions": "Trading only - no withdrawal",
                "real_trading": not getattr(broker, 'paper_mode', True),
            }
            with self._lock:
                self.brokers[broker_id] = broker
                self.broker_configs[broker_id] = cfg

        elif broker_type == "coindcx":
            if not api_key or not api_secret:
                raise ValueError("CoinDCX requires API key and secret for real money trading")
            if len(api_key.strip()) < 8 or len(api_secret.strip()) < 8:
                raise ValueError("API keys too short - check CoinDCX API dashboard")
            broker = CoinDCXBroker()
            success = broker.connect(api_key.strip(), api_secret.strip())
            if not success:
                raise ValueError("Failed to connect to CoinDCX - check API keys, trading permission, IP whitelist")

            cfg = {
                "id": broker_id,
                "name": "CoinDCX REAL MONEY",
                "type": "coindcx",
                "api_key_encoded": self._encode(api_key.strip()),
                "api_secret_encoded": self._encode(api_secret.strip()),
                "has_keys": True,
                "paper_mode": False,
                "connected": True,
                "real_trading": True,
                "created_at": datetime.utcnow().isoformat(),
                "warning": "REAL MONEY - Actual INR from CoinDCX account",
                "markets": "BTCINR, ETHINR, BNBINR, SOLINR, XRPINR, ADAINR, etc.",
                "secure": "Keys encoded, trading permission only",
                "actual_money": "Uses actual CoinDCX INR balance"
            }
            with self._lock:
                self.brokers[broker_id] = broker
                self.broker_configs[broker_id] = cfg

        elif broker_type == "paper":
            broker = PaperBroker(initial_balance=initial_balance)
            try:
                broker.connect()
            except Exception as e:
                logger.warning(f"Paper broker connect failed: {e}")
            cfg = {
                "id": broker_id,
                "name": "Paper Trading (Testing Only)",
                "type": "paper",
                "initial_balance": initial_balance,
                "paper_mode": True,
                "connected": True,
                "created_at": datetime.utcnow().isoformat(),
                "real_trading": False,
                "note": "Paper for testing only"
            }
            with self._lock:
                self.brokers[broker_id] = broker
                self.broker_configs[broker_id] = cfg

        self.save()
        with self._lock:
            broker_obj = self.brokers.get(broker_id)
            paper_mode = getattr(broker_obj, 'paper_mode', True) if broker_obj else True
        logger.info(f"Added broker {broker_id} type {broker_type} paper_mode={paper_mode}")
        with self._lock:
            return dict(self.broker_configs[broker_id])

    def get_broker(self, broker_id: str) -> Optional[BaseBroker]:
        if not broker_id:
            return None
        with self._lock:
            return self.brokers.get(broker_id)

    def get_all_brokers(self) -> Dict:
        result = {}
        with self._lock:
            configs = dict(self.broker_configs)
            brokers = dict(self.brokers)
        for broker_id, cfg in configs.items():
            broker = brokers.get(broker_id)
            balance_info = {}
            # Only fetch balances if broker is connected and not paper? But paper also has balances
            # Avoid network call for disconnected CoinDCX to prevent slowdown
            if broker and getattr(broker, 'connected', False):
                try:
                    # For paper, quick
                    if cfg.get("type") == "paper":
                        balances = broker.get_balance()
                        balance_info = {k: v.to_dict() for k, v in balances.items()}
                    else:
                        # For real brokers, try but don't fail if slow
                        # Skip balance fetch in get_all to avoid blocking - let dedicated /balance endpoint handle
                        # Instead just indicate connected
                        balance_info = {"info": "Use /brokers/{id}/balance for live balances"}
                except Exception as e:
                    logger.debug(f"Balance fetch failed for {broker_id}: {e}")
                    balance_info = {}
            result[broker_id] = {
                **cfg,
                "balances": balance_info,
                "api_key_preview": (cfg.get("api_key_encoded", "")[:10] + "..." if cfg.get("api_key_encoded") else None) if cfg.get("has_keys") else None,
                "secure_note": "Keys encoded, trading permission only"
            }
        return result

    def remove_broker(self, broker_id: str) -> bool:
        if not broker_id:
            return False
        broker_id = broker_id.strip().lower()
        if broker_id == "paper":
            raise ValueError("Cannot remove default paper broker")
        with self._lock:
            if broker_id in self.brokers:
                del self.brokers[broker_id]
            if broker_id in self.broker_configs:
                del self.broker_configs[broker_id]
                # Save outside lock to avoid deadlock
                to_save = True
            else:
                to_save = False
        if to_save:
            self.save()
            return True
        return False

    def test_broker(self, broker_id: str) -> Dict:
        if not broker_id:
            return {"connected": False, "error": "broker_id required"}
        broker = self.get_broker(broker_id)
        if not broker:
            return {"connected": False, "error": "Broker not found"}
        try:
            return broker.test_connection()
        except Exception as e:
            logger.warning(f"Test broker {broker_id} failed: {e}")
            return {"connected": False, "error": str(e)}

_broker_manager = None
_manager_lock = threading.Lock()

def get_broker_manager() -> BrokerManager:
    global _broker_manager
    if _broker_manager is None:
        with _manager_lock:
            if _broker_manager is None:
                _broker_manager = BrokerManager()
    return _broker_manager
