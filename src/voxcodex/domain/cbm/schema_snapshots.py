from __future__ import annotations

import json
from pathlib import Path
from typing import TypeAlias

from pydantic import BaseModel

from voxcodex.domain.cbm.content import ContentFragment, DocumentNode, FidelityConstraint
from voxcodex.domain.cbm.document import CanonicalDocument, CanonicalRevision
from voxcodex.domain.cbm.provenance import SourceAnchor
from voxcodex.domain.cbm.semantic import Annotation, Entity, Relation
from voxcodex.domain.cbm.structured import FormulaPayload, TablePayload
from voxcodex.domain.cbm.validation import ValidationPolicy, ValidationReport
from voxcodex.domain.processing import Derivation, ProcessingActivity


ModelType: TypeAlias = type[BaseModel]

SCHEMA_MODELS: dict[str, ModelType] = {
    "annotation": Annotation,
    "canonical-document": CanonicalDocument,
    "canonical-revision": CanonicalRevision,
    "content-fragment": ContentFragment,
    "derivation": Derivation,
    "document-node": DocumentNode,
    "entity": Entity,
    "fidelity-constraint": FidelityConstraint,
    "formula-payload": FormulaPayload,
    "processing-activity": ProcessingActivity,
    "relation": Relation,
    "source-anchor": SourceAnchor,
    "table-payload": TablePayload,
    "validation-policy": ValidationPolicy,
    "validation-report": ValidationReport,
}


def schema_text(model: ModelType) -> str:
    schema = model.model_json_schema(mode="validation")
    return json.dumps(schema, ensure_ascii=False, sort_keys=True, indent=2) + "\n"


def write_schema_snapshots(root: Path) -> tuple[Path, ...]:
    root.mkdir(parents=True, exist_ok=True)
    paths: list[Path] = []
    for name, model in sorted(SCHEMA_MODELS.items()):
        path = root / f"{name}.schema.json"
        path.write_text(schema_text(model), encoding="utf-8")
        paths.append(path)
    return tuple(paths)


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    write_schema_snapshots(args.output)


if __name__ == "__main__":
    main()
