import argparse
import sys
import os

# Add root directory to path so we can import the extractor
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from core.autonomous_dev.repository_extractor import RepositoryExtractor

def main():
    parser = argparse.ArgumentParser(description="DGM-MAT Repository Extraction CLI")
    parser.add_argument("component", choices=["runtime", "providers", "memory", "cockpit"],
                        help="The component to extract into a satellite repository.")
    parser.add_argument("--dry-run", action="store_true", help="Run the extraction without copying any files.")
    parser.add_argument("--manifest", default="config/extraction_manifest.json", help="Path to the extraction manifest.")

    args = parser.parse_args()

    extractor = RepositoryExtractor(manifest_path=args.manifest)
    success = extractor.extract(args.component, dry_run=args.dry_run)

    if success:
        print(f"Successfully processed extraction for '{args.component}'.")
        sys.exit(0)
    else:
        print(f"Failed to process extraction for '{args.component}'.")
        sys.exit(1)

if __name__ == "__main__":
    main()
