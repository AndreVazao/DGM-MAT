from pathlib import Path


def test_windows_build_upload_uses_github_environment_expression():
    workflow = (
        Path(__file__).resolve().parents[2]
        / ".github"
        / "workflows"
        / "build-windows.yml"
    ).read_text(encoding="utf-8")

    upload_step = workflow.split("      - name: Upload Build Artifacts", 1)[1]

    assert "${{ env.VERSION }}" in upload_step
    assert "$env:VERSION" not in upload_step
    assert "if-no-files-found: error" in upload_step


def test_windows_build_asserts_zip_and_checksum_before_upload():
    workflow = (
        Path(__file__).resolve().parents[2]
        / ".github"
        / "workflows"
        / "build-windows.yml"
    ).read_text(encoding="utf-8")

    assertions = workflow.split("      - name: Final Build Assertions", 1)[1].split(
        "      - name: Upload Build Artifacts", 1
    )[0]

    assert "Distribution ZIP missing" in assertions
    assert "SHA-256 file missing" in assertions
    assert "valid digest" in assertions
