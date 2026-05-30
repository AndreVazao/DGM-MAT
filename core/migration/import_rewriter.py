import ast
import astor
from typing import Dict

class ImportRewriter:
    def __init__(self, import_map: Dict[str, str] = None):
        """
        import_map: Mapping of old module names to new module names.
        Example: {"core.api": "dgm_core.api"}
        """
        self.import_map = import_map or {}

    def rewrite_content(self, content: str) -> str:
        try:
            tree = ast.parse(content)
        except SyntaxError:
            return content

        modified = False
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    if alias.name in self.import_map:
                        alias.name = self.import_map[alias.name]
                        modified = True
            elif isinstance(node, ast.ImportFrom):
                if node.module in self.import_map:
                    node.module = self.import_map[node.module]
                    modified = True
                elif node.module:
                    # Check for partial matches
                    for old_mod, new_mod in self.import_map.items():
                        if node.module.startswith(old_mod + "."):
                            node.module = node.module.replace(old_mod, new_mod, 1)
                            modified = True
                            break

        if modified:
            return astor.to_source(tree)
        return content

    def update_map(self, old_mod: str, new_mod: str):
        self.import_map[old_mod] = new_mod
