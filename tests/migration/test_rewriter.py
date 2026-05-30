import pytest
from core.migration.import_rewriter import ImportRewriter

def test_rewrite_content():
    rewriter = ImportRewriter({"core.api": "dgm_core.api"})
    content = "import core.api\nfrom core.api import Client"

    rewritten = rewriter.rewrite_content(content)
    assert "import dgm_core.api" in rewritten
    assert "from dgm_core.api import Client" in rewritten

def test_rewrite_partial_match():
    rewriter = ImportRewriter({"core": "dgm_core"})
    content = "from core.runtime.state import Store"

    rewritten = rewriter.rewrite_content(content)
    assert "from dgm_core.runtime.state import Store" in rewritten
