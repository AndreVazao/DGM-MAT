from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from datetime import datetime

@dataclass
class AutonomousTask:
    task_id: str
    title: str
    description: str
    priority: int
    assigned_agent: str
    status: str
    origin: str  # e.g., "repo_analysis", "failed_execution", "provider_sync"
    repo: Optional[str] = None
    confidence: float = 1.0
    risk: str = "LOW"
    execution_type: str = "SAFE" # SAFE, EXPERIMENTAL, SYSTEM
    dependencies: List[str] = field(default_factory=list)
    estimated_impact: str = "LOW"
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)

@dataclass
class RepoAnalysisReport:
    repo_id: str
    timestamp: datetime
    dead_code: List[str]
    duplicates: List[Dict[str, Any]]
    architecture_drift: List[str]
    outdated_dependencies: List[Dict[str, str]]
    score: int
