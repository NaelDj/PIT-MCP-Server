from pathlib import Path
import sys
import json
import xml.etree.ElementTree as ET
from collections import defaultdict

VALID_STATUSES = {
    "KILLED",
    "SURVIVED",
    "NO_COVERAGE",
    "TIMED_OUT",
    "NON_VIABLE",
    "MEMORY_ERROR",
    "RUN_ERROR",
}

DETECTED_STATUSES = {"KILLED", "TIMED_OUT"}                     # mutants whose effects were observed (killed, timed out)
COVERED_STATUSES = {"KILLED", "SURVIVED", "TIMED_OUT"}          # mutants executed by the tests
TOTAL = COVERED_STATUSES.union({"NO_COVERAGE"})                 # all mutants that were generated
ERROR_STATUSES = {"NON_VIABLE", "MEMORY_ERROR", "RUN_ERROR"}

def pit_classes_from_xml(xml_path: Path, include_details: bool = True):
    if not xml_path.exists():
        raise FileNotFoundError(f"PIT report not found: {xml_path}")

    tree = ET.parse(xml_path)
    root = tree.getroot()

    # class -> counters
    stats = defaultdict(
        lambda: {
            "byStatus": defaultdict(int),
            "total": 0,
            "covered": 0, # killed + survived + timeouts
            "detected": 0, # killed + timeouts
            "errors": 0,
        }
    )

    for mutation in root.findall("mutation"):
        status = mutation.get("status")
        mutated_class = mutation.findtext("mutatedClass")
        if not mutated_class or not status:
            continue

        # Track status counts (helps debugging / later metrics)
        stats[mutated_class]["byStatus"][status] += 1

        # For "test strength"/covered-based scores:
        if status in COVERED_STATUSES:
            stats[mutated_class]["covered"] += 1

        if status in DETECTED_STATUSES:
            stats[mutated_class]["detected"] += 1

        # For "mutation coverage" total denominator:
        # Count NO_COVERAGE too, but exclude error statuses by default
        if status in TOTAL:
            stats[mutated_class]["total"] += 1

        # Count errors separately (optional)
        if status in ERROR_STATUSES:
            stats[mutated_class]["errors"] += 1


    # Build final result
    result = []
    for cls, data in stats.items():
        total = data["total"]
        covered = data["covered"]
        detected = data["detected"]
        no_coverage = data["byStatus"].get("NO_COVERAGE", 0)

        # When tests reach code, how often do they detect faults?
        test_strength = detected / covered if covered > 0 else None
        # Out of all mutants in the code, how often are faults detected?
        # A mutant that is never executed is still a missed detection
        mutation_coverage = detected / total if total > 0 else None

        score = round(test_strength, 3) if test_strength is not None else None

        row = {"class": cls, "mutationScore": score}

        if include_details:
            # add extra context only when you want it
            row.update({
                "survived": covered-detected,
                "killed": detected,
                "noCoverage": no_coverage,
            })

        result.append(row)

    # Sort: lowest mutation score first (hotspots)
    result.sort(key=lambda x: (x["mutationScore"] is None, x["mutationScore"]))

    return result

def find_latest_pit_xml(workspace: Path) -> Path:
    pit_root = workspace / "target" / "pit-reports"
    if not pit_root.exists():
        raise FileNotFoundError(f"No {pit_root} directory found")

    # Case 1: non-timestamped layout (direct file)
    direct = pit_root / "mutations.xml"
    if direct.exists():
        return direct

    # Case 2: timestamped subfolders
    candidates = []
    for p in pit_root.iterdir():
        if p.is_dir():
            m = p / "mutations.xml"
            if m.exists():
                candidates.append(m)

    if not candidates:
        raise FileNotFoundError(f"No mutations.xml found in {pit_root} (directly or in subfolders)")

    return max(candidates, key=lambda p: p.stat().st_mtime)

def pit_classes(workspace: Path):
    xml_path = find_latest_pit_xml(workspace)
    return pit_classes_from_xml(xml_path)

def pit_methods_from_xml(xml_path: Path, class_name: str, include_details: bool = True):
    if not xml_path.exists():
        raise FileNotFoundError(f"PIT report not found: {xml_path}")

    tree = ET.parse(xml_path)
    root = tree.getroot()

    # (mutatedMethod, methodDescription) -> counters
    stats = defaultdict(
        lambda: {
            "byStatus": defaultdict(int),
            "total": 0,
            "covered": 0,
            "detected": 0,
            "errors": 0,
        }
    )

    for mutation in root.findall("mutation"):
        status = mutation.get("status")
        mutated_class = mutation.findtext("mutatedClass")
        if not mutated_class or not status:
            continue

        if mutated_class != class_name:
            continue

        mutated_method = mutation.findtext("mutatedMethod") or "<unknownMethod>"
        method_desc = mutation.findtext("methodDescription") or ""

        key = (mutated_method, method_desc)

        # Track status counts
        stats[key]["byStatus"][status] += 1

        # Covered / detected
        if status in COVERED_STATUSES:
            stats[key]["covered"] += 1
        if status in DETECTED_STATUSES:
            stats[key]["detected"] += 1

        # Total denominator (covered + no_coverage)
        if status in TOTAL:
            stats[key]["total"] += 1

        # Errors separately
        if status in ERROR_STATUSES:
            stats[key]["errors"] += 1

    # Build final result
    result = []
    for (method, desc), data in stats.items():
        total = data["total"]
        covered = data["covered"]
        detected = data["detected"]
        no_coverage = data["byStatus"].get("NO_COVERAGE", 0)

        # Test strength: detected / covered, undefined when covered==0
        test_strength = detected / covered if covered > 0 else None
        score = round(test_strength, 3) if test_strength is not None else None

        row = {
            # "class": class_name,
            "method": method,
            "methodDesc": desc,
            "mutationScore": score,
        }

        if include_details:
            row.update({
                "survived": covered - detected,
                "killed": detected,
                "noCoverage": no_coverage,
            })

        result.append(row)

    # Sort: lowest score first; null last
    result.sort(key=lambda x: (x["mutationScore"] is None, x["mutationScore"]))

    return result

def pit_methods(workspace: Path, class_name: str, include_details: bool = True):
    xml_path = find_latest_pit_xml(workspace)
    return pit_methods_from_xml(xml_path, class_name=class_name, include_details=include_details)

if __name__ == "__main__":

    # Testing classes
    # xml_path = Path(sys.argv[1])
    # result = find_latest_pit_xml(xml_path)
    # print(result)
    # result = pit_classes_from_xml(xml_path)
    # print(json.dumps(result, indent=2, sort_keys=False))

    # Testing methods
    xml_path = Path(sys.argv[1])
    class_name = sys.argv[2]
    result = pit_methods_from_xml(xml_path, class_name=class_name)
    print(json.dumps(result, indent=2, sort_keys=False))