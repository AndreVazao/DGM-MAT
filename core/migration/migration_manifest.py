from enum import Enum
from typing import List, Dict, Optional
from pydantic import BaseModel, Field

class ModuleCategory(str, Enum):
    CORE = "CORE"
    OPTIONAL = "OPTIONAL"
    LEGACY = "LEGACY"
    DUPLICATE = "DUPLICATE"
    EXPERIMENTAL = "EXPERIMENTAL"
    ORPHAN = "ORPHAN"

class ModuleInventoryItem(BaseModel):
    path: str
    dependency_count: int = 0
    import_count: int = 0
    file_size: int = 0
    risk_score: float = 0.0
    category: ModuleCategory = ModuleCategory.EXPERIMENTAL
    dependencies: List[str] = []
    dependents: List[str] = []
    hash: str = ""

class ModuleInventory(BaseModel):
    modules: Dict[str, ModuleInventoryItem] = {}

class MigrationPlanItem(BaseModel):
    source_path: str
    target_path: str
    action: str = "COPY"
    status: str = "PENDING"

class MigrationPlan(BaseModel):
    items: List[MigrationPlanItem] = []
    version: str = "1.0.0"

class DuplicateReport(BaseModel):
    duplicates: Dict[str, List[str]] = {}

class OrphanReport(BaseModel):
    orphans: List[str] = []
