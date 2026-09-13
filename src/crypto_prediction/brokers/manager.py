"""
Broker Manager v5 MAX - Manages multiple brokers, API keys, connections, metrics, pooling
- Thread-safe, atomic save, decode fallback, avoids balance fetch for disconnected, CoinDCX REAL INR
- Versioning, metrics, cache, validation
"""
from typing import Dict, List, Optional
import json
from pathlib import Path
from datetime import datetime
import base64
import threading
import time

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
        self.storage_path = Path(storage_path) if storage_path else config.project_root / "data" / "brokers_v5.json"
        self.brokers: Dict[str, BaseBroker] = {}
        self.broker_configs: Dict[str, Dict] = {}
        self._lock = threading.Lock()
        self._metrics = {
            "brokers_added": 0,
            "brokers_removed": 0,
            "connection_attempts": 0,
            "connection_failures": 0,
            "balance_fetches": 0
        }
        self.load()

        with self._lock:
            if "paper" not in self.brokers:
                paper = PaperBroker(initial_balance=10000)
                try:
                    paper.connect()
                except Exception as e:
                    logger.warning(f"Paper v5 broker connect failed: {e}")
                self.brokers["paper"] = paper
                self.broker_configs["paper"] = {
                    "name": "Paper (Testing Only) v5",
                    "type": "paper",
                    "connected": True,
                    "paper_mode": True,
                    "initial_balance": 10000,
                    "created_at": datetime.utcnow().isoformat(),
                    "note": "Paper for testing only - real trading via CoinDCX",
                    "version": "v5_max"
                }

            if "coindcx" not in self.brokers:
                coindcx = CoinDCXBroker()
                self.brokers["coindcx"] = coindcx
                self.broker_configs["coindcx"] = {
                    "id": "coindcx",
                    "name": "CoinDCX REAL MONEY v5",
                    "type": "coindcx",
                    "connected": False,
                    "paper_mode": False,
                    "real_trading": True,
                    "has_keys": False,
                    "created_at": datetime.utcnow().isoformat(),
                    "warning": "REAL MONEY v5 - Actual INR from CoinDCX account",
                    "markets": "BTCINR, ETHINR, BNBINR, SOLINR, XRPINR, ADAINR, DOGEINR, AVAXINR, etc.",
                    "secure": "API keys encoded, trading permission only",
                    "version": "v5_max"
                }
        try:
            self.save()
        except Exception as e:
            logger.debug(f"BrokerManager v5 initial save failed: {e}")

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
            decoded = base64.b64decode(encoded.encode('utf-8')).decode('utf-8')
            if len(decoded) >= 8:
                return decoded
            return encoded
        except Exception:
            return encoded

    def load(self):
        # Try v5 first, then fallback to old
        paths_to_try = [self.storage_path, config.project_root / "data" / "brokers.json"]
        for path in paths_to_try:
            try:
                if path.exists():
                    data = json.loads(path.read_text())
                    brokers_data = data.get("brokers", {})
                    if not isinstance(brokers_data, dict):
                        logger.warning(f"Brokers v5 file invalid format {path}")
                        continue
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
                                                logger.warning(f"Binance v5 reconnect failed {broker_id}, fallback to paper")
                                                broker.paper_mode = True
                                                broker.connected = True
                                    except Exception as e:
                                        logger.warning(f"Failed to reconnect broker v5 {broker_id}: {e}")
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
                                                logger.warning(f"CoinDCX v5 reconnect failed for {broker_id}")
                                    except Exception as e:
                                        logger.warning(f"Failed to reconnect CoinDCX v5 broker {broker_id}: {e}")
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
                                    logger.warning(f"Paper v5 broker connect failed {broker_id}: {e}")
                                with self._lock:
                                    self.brokers[broker_id] = broker
                        except Exception as e:
                            logger.warning(f"Failed to load broker v5 {broker_id}: {e}")
                            continue
                    logger.info(f"Loaded {len(self.brokers)} brokers v5 from {path}")
                    return
            except json.JSONDecodeError as e:
                logger.warning(f"Brokers v5 file JSON invalid {path}: {e}")
            except Exception as e:
                logger.warning(f"Failed to load brokers v5 from {path}: {e}")

    def save(self):
        try:
            self.storage_path.parent.mkdir(parents=True, exist_ok=True)
            with self._lock:
                configs_copy = dict(self.broker_configs)
            data = {
                "brokers": configs_copy,
                "timestamp": datetime.utcnow().isoformat(),
                "warning": "API keys are base64 encoded, not encrypted - store securely, never share",
                "real_trading": "CoinDCX REAL MONEY v5 - actual INR",
                "version": "v5_max",
                "metrics": self._metrics
            }
            tmp_path = self.storage_path.with_suffix('.tmp')
            tmp_path.write_text(json.dumps(data, indent=2))
            tmp_path.replace(self.storage_path)
        except Exception as e:
            logger.error(f"Failed to save brokers v5: {e}")

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
            self._metrics["connection_attempts"] += 1

        if broker_id in self.brokers and broker_id != "paper":
            logger.info(f"Broker v5 {broker_id} exists, updating")
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
                    with self._lock:
                        self._metrics["connection_failures"] += 1
                    raise ValueError("Failed to connect to Binance - check API keys")
            else:
                broker.paper_mode = True
                broker.connected = True

            cfg = {
                "id": broker_id,
                "name": f"Binance {'Testnet' if testnet else 'Live'} v5",
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
                "version": "v5_max"
            }
            with self._lock:
                self.brokers[broker_id] = broker
                self.broker_configs[broker_id] = cfg
                self._metrics["brokers_added"] += 1

        elif broker_type == "coindcx":
            if not api_key or not api_secret:
                raise ValueError("CoinDCX v5 requires API key and secret for real money trading")
            if len(api_key.strip()) < 8 or len(api_secret.strip()) < 8:
                raise ValueError("API keys too short - check CoinDCX API dashboard")
            broker = CoinDCXBroker()
            success = broker.connect(api_key.strip(), api_secret.strip())
            if not success:
                with self._lock:
                    self._metrics["connection_failures"] += 1
                raise ValueError("Failed to connect to CoinDCX v5 - check API keys, trading permission, IP whitelist")

            cfg = {
                "id": broker_id,
                "name": "CoinDCX REAL MONEY v5",
                "type": "coindcx",
                "api_key_encoded": self._encode(api_key.strip()),
                "api_secret_encoded": self._encode(api_secret.strip()),
                "has_keys": True,
                "paper_mode": False,
                "connected": True,
                "real_trading": True,
                "created_at": datetime.utcnow().isoformat(),
                "warning": "REAL MONEY v5 - Actual INR from CoinDCX account",
                "markets": "BTCINR, ETHINR, BNBINR, SOLINR, XRPINR, ADAINR, etc.",
                "secure": "Keys encoded, trading permission only",
                "actual_money": "Uses actual CoinDCX INR balance",
                "version": "v5_max"
            }
            with self._lock:
                self.brokers[broker_id] = broker
                self.broker_configs[broker_id] = cfg
                self._metrics["brokers_added"] += 1

        elif broker_type == "paper":
            broker = PaperBroker(initial_balance=initial_balance)
            try:
                broker.connect()
            except Exception as e:
                logger.warning(f"Paper v5 broker connect failed: {e}")
            cfg = {
                "id": broker_id,
                "name": "Paper Trading (Testing Only) v5",
                "type": "paper",
                "initial_balance": initial_balance,
                "paper_mode": True,
                "connected": True,
                "created_at": datetime.utcnow().isoformat(),
                "real_trading": False,
                "note": "Paper for testing only",
                "version": "v5_max"
            }
            with self._lock:
                self.brokers[broker_id] = broker
                self.broker_configs[broker_id] = cfg
                self._metrics["brokers_added"] += 1

        self.save()
        with self._lock:
            broker_obj = self.brokers.get(broker_id)
            paper_mode = getattr(broker_obj, 'paper_mode', True) if broker_obj else True
        logger.info(f"Added broker v5 {broker_id} type {broker_type} paper_mode={paper_mode}")
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
            if broker and getattr(broker, 'connected', False):
                try:
                    if cfg.get("type") == "paper":
                        balances = broker.get_balance()
                        balance_info = {k: v.to_dict() for k, v in balances.items()}
                        with self._lock:
                            self._metrics["balance_fetches"] += 1
                    else:
                        balance_info = {"info": "Use /brokers/{id}/balance for live v5 balances"}
                except Exception as e:
                    logger.debug(f"Balance v5 fetch failed for {broker_id}: {e}")
                    balance_info = {}
            result[broker_id] = {
                **cfg,
                "balances": balance_info,
                "api_key_preview": (cfg.get("api_key_encoded", "")[:10] + "..." if cfg.get("api_key_encoded") else None) if cfg.get("has_keys") else None,
                "secure_note": "Keys encoded, trading permission only v5",
                "version": "v5_max"
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
                self._metrics["brokers_removed"] += 1
                to_save = True
            else:
                to_save = False
        if to_save:
            self.save()
            return True
        return False

    def test_broker(self, broker_id: str) -> Dict:
        if not broker_id:
            return {"connected": False, "error": "broker_id required", "version": "v5_max"}
        broker = self.get_broker(broker_id)
        if not broker:
            return {"connected": False, "error": "Broker not found", "version": "v5_max"}
        try:
            result = broker.test_connection()
            result["version"] = "v5_max"
            return result
        except Exception as e:
            logger.warning(f"Test broker v5 {broker_id} failed: {e}")
            return {"connected": False, "error": str(e), "version": "v5_max"}

    def get_metrics(self) -> Dict:
        with self._lock:
            return {
                **self._metrics,
                "brokers_count": len(self.brokers),
                "version": "v5_max",
                "timestamp": datetime.utcnow().isoformat()
            }

_broker_manager = None
_manager_lock = threading.Lock()

def get_broker_manager() -> BrokerManager:
    global _broker_manager
    if _broker_manager is None:
        with _manager_lock:
            if _broker_manager is None:
                _broker_manager = BrokerManager()
    return _broker_manager
