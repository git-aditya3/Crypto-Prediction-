"""
Trading Journal - Log real trades with notes, emotions, lessons
For actual trading improvement
"""
from dataclasses import dataclass, asdict
from typing import Dict, List, Optional
from datetime import datetime
import json
from pathlib import Path
import uuid

from ..config import get_config
from ..utils.logger import get_logger

logger = get_logger(__name__)
config = get_config()

@dataclass
class JournalEntry:
    id: str
    symbol: str
    side: str
    entry_price: float
    exit_price: Optional[float]
    quantity: float
    pnl: float
    pnl_pct: float
    entry_time: str
    exit_time: Optional[str]
    strategy: str
    notes: str
    emotions: str
    lessons: str
    tags: List[str]
    status: str
    timestamp: str

class JournalManager:
    def __init__(self, storage_path: str = None):
        self.storage_path = Path(storage_path) if storage_path else config.project_root / "data" / "journal.json"
        self.entries: Dict[str, JournalEntry] = {}
        self.load()
    
    def load(self):
        try:
            if self.storage_path.exists():
                data = json.loads(self.storage_path.read_text())
                for entry_data in data.get("entries", []):
                    entry = JournalEntry(**entry_data)
                    self.entries[entry.id] = entry
        except Exception as e:
            logger.warning(f"Failed to load journal: {e}")
    
    def save(self):
        try:
            self.storage_path.parent.mkdir(parents=True, exist_ok=True)
            data = {
                "entries": [asdict(e) for e in self.entries.values()],
                "timestamp": datetime.utcnow().isoformat()
            }
            self.storage_path.write_text(json.dumps(data, indent=2))
        except Exception as e:
            logger.error(f"Failed to save journal: {e}")
    
    def add_entry(self, symbol: str, side: str, entry_price: float, quantity: float, 
                  strategy: str = "AI Ensemble", notes: str = "", emotions: str = "", 
                  lessons: str = "", tags: List[str] = None, exit_price: float = None, pnl: float = 0) -> JournalEntry:
        entry_id = str(uuid.uuid4())[:8]
        
        pnl_pct = 0
        if exit_price and entry_price:
            if side == "LONG":
                pnl_pct = (exit_price - entry_price) / entry_price * 100
            else:
                pnl_pct = (entry_price - exit_price) / entry_price * 100
        
        entry = JournalEntry(
            id=entry_id,
            symbol=symbol,
            side=side,
            entry_price=entry_price,
            exit_price=exit_price,
            quantity=quantity,
            pnl=pnl,
            pnl_pct=pnl_pct,
            entry_time=datetime.utcnow().isoformat(),
            exit_time=datetime.utcnow().isoformat() if exit_price else None,
            strategy=strategy,
            notes=notes,
            emotions=emotions,
            lessons=lessons,
            tags=tags or [],
            status="CLOSED" if exit_price else "OPEN",
            timestamp=datetime.utcnow().isoformat()
        )
        
        self.entries[entry_id] = entry
        self.save()
        logger.info(f"Added REAL journal entry: {entry_id} {symbol} {side} P&L ${pnl:.2f}")
        return entry
    
    def get_entries(self, symbol: str = None, tag: str = None) -> List[Dict]:
        entries = list(self.entries.values())
        
        if symbol:
            entries = [e for e in entries if e.symbol == symbol]
        if tag:
            entries = [e for e in entries if tag in e.tags]
        
        # Sort by timestamp desc
        entries.sort(key=lambda x: x.timestamp, reverse=True)
        return [asdict(e) for e in entries]
    
    def get_stats(self) -> Dict:
        entries = list(self.entries.values())
        closed = [e for e in entries if e.status == "CLOSED"]
        
        total_pnl = sum(e.pnl for e in closed)
        wins = [e for e in closed if e.pnl > 0]
        
        return {
            "total_entries": len(entries),
            "closed": len(closed),
            "open": len(entries) - len(closed),
            "total_pnl": total_pnl,
            "win_rate": len(wins) / len(closed) * 100 if closed else 0,
            "avg_pnl": total_pnl / len(closed) if closed else 0,
            "real_trading": True
        }

def get_journal_manager():
    return JournalManager()
