"""Challenge IV end-to-end demo endpoints.

This router provides a fully self-contained RFP → match → price pipeline
using mock data so the frontend can demonstrate the complete flow without
additional setup. The data is intentionally small and deterministic so the
UI can render quickly and predictably.
"""
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, Query

router = APIRouter(prefix="/api/challenge", tags=["Challenge"])


# ---------- Mock Data ----------
def _mock_rfps() -> List[Dict[str, Any]]:
    today = datetime.utcnow()
    return [
        {
            "id": "rfp-metro-ht",
            "title": "Metro Rail Project - HT XLPE Cables",
            "due_date": (today + timedelta(days=45)).isoformat(),
            "estimated_value": 2.5e7,
            "strategic_fit": "high",
            "category": "cable",
            "download_url": "https://example.com/rfp/metro-ht.pdf",
        },
        {
            "id": "rfp-airport-lv",
            "title": "Airport Expansion - LV Power & Control Cables",
            "due_date": (today + timedelta(days=32)).isoformat(),
            "estimated_value": 1.6e7,
            "strategic_fit": "medium",
            "category": "cable",
            "download_url": "https://example.com/rfp/airport-lv.pdf",
        },
        {
            "id": "rfp-psu-fmeg",
            "title": "PSU Modernization - FMEG & Wiring",
            "due_date": (today + timedelta(days=25)).isoformat(),
            "estimated_value": 1.1e7,
            "strategic_fit": "high",
            "category": "fmeg",
            "download_url": "https://example.com/rfp/psu-fmeg.pdf",
        },
    ]


def _mock_items(rfp_id: str) -> List[Dict[str, Any]]:
    """Return a deterministic scope of supply for the demo RFP."""
    if rfp_id == "rfp-metro-ht":
        return [
            {
                "item_id": "line-1",
                "description": "11 kV XLPE Armored Cable",
                "quantity": 5000,
                "unit": "m",
                "requirements": {
                    "voltage_kv": 11,
                    "conductor_size_sqmm": 240,
                    "core_count": 3,
                    "insulation": "XLPE",
                    "armoring": "SWA",
                    "standard": "IS-7098",
                },
            },
            {
                "item_id": "line-2",
                "description": "11 kV XLPE Single Core",
                "quantity": 3200,
                "unit": "m",
                "requirements": {
                    "voltage_kv": 11,
                    "conductor_size_sqmm": 95,
                    "core_count": 1,
                    "insulation": "XLPE",
                    "armoring": "AWA",
                    "standard": "IS-7098",
                },
            },
        ]
    if rfp_id == "rfp-airport-lv":
        return [
            {
                "item_id": "line-1",
                "description": "1.1 kV CU XLPE Control Cable",
                "quantity": 4200,
                "unit": "m",
                "requirements": {
                    "voltage_kv": 1.1,
                    "conductor_size_sqmm": 35,
                    "core_count": 4,
                    "insulation": "XLPE",
                    "armoring": "SWA",
                    "standard": "IS-1554",
                },
            }
        ]
    return [
        {
            "item_id": "line-1",
            "description": "1.1 kV CU FRLS House Wire",
            "quantity": 10000,
            "unit": "m",
            "requirements": {
                "voltage_kv": 1.1,
                "conductor_size_sqmm": 6,
                "core_count": 1,
                "insulation": "FRLS",
                "armoring": "None",
                "standard": "IS-694",
            },
        }
    ]


def _product_catalog() -> List[Dict[str, Any]]:
    return [
        {
            "sku": "XLPE-11KV-240-3C-SWA",
            "name": "11 kV XLPE 240 sqmm 3C SWA",
            "voltage_kv": 11,
            "conductor_size_sqmm": 240,
            "core_count": 3,
            "insulation": "XLPE",
            "armoring": "SWA",
            "standard": "IS-7098",
            "unit_price": 1850.0,
        },
        {
            "sku": "XLPE-11KV-120-3C-SWA",
            "name": "11 kV XLPE 120 sqmm 3C SWA",
            "voltage_kv": 11,
            "conductor_size_sqmm": 120,
            "core_count": 3,
            "insulation": "XLPE",
            "armoring": "SWA",
            "standard": "IS-7098",
            "unit_price": 1180.0,
        },
        {
            "sku": "XLPE-11KV-95-1C-AWA",
            "name": "11 kV XLPE 95 sqmm 1C AWA",
            "voltage_kv": 11,
            "conductor_size_sqmm": 95,
            "core_count": 1,
            "insulation": "XLPE",
            "armoring": "AWA",
            "standard": "IS-7098",
            "unit_price": 620.0,
        },
        {
            "sku": "CU-1KV-35-4C-SWA",
            "name": "1.1 kV CU XLPE 35 sqmm 4C SWA",
            "voltage_kv": 1.1,
            "conductor_size_sqmm": 35,
            "core_count": 4,
            "insulation": "XLPE",
            "armoring": "SWA",
            "standard": "IS-1554",
            "unit_price": 210.0,
        },
        {
            "sku": "CU-1KV-6-1C-FRLS",
            "name": "1.1 kV CU FRLS 6 sqmm 1C",
            "voltage_kv": 1.1,
            "conductor_size_sqmm": 6,
            "core_count": 1,
            "insulation": "FRLS",
            "armoring": "None",
            "standard": "IS-694",
            "unit_price": 32.0,
        },
    ]


def _test_catalog() -> List[Dict[str, Any]]:
    return [
        {"code": "HV", "name": "High Voltage Test", "unit_price": 25000},
        {"code": "IR", "name": "Insulation Resistance", "unit_price": 8000},
        {"code": "TS", "name": "Tensile Strength", "unit_price": 12000},
        {"code": "SI", "name": "Sheath Integrity", "unit_price": 9000},
    ]


# ---------- Helpers ----------
def _score_product(requirements: Dict[str, Any], product: Dict[str, Any]) -> Dict[str, Any]:
    """Simple equal-weight spec match."""
    specs = ["voltage_kv", "conductor_size_sqmm", "core_count", "insulation", "armoring", "standard"]
    matched = 0
    details = []

    for spec in specs:
        req_val = requirements.get(spec)
        prod_val = product.get(spec)

        if req_val is None or prod_val is None:
            details.append({"spec": spec, "status": "unknown"})
            continue

        status = "match"
        if isinstance(req_val, (int, float)) and isinstance(prod_val, (int, float)):
            # Allow 5% tolerance
            if prod_val == 0:
                status = "mismatch"
            else:
                diff = abs(req_val - prod_val) / prod_val
                status = "match" if diff <= 0.05 else "mismatch"
        else:
            status = "match" if str(req_val).lower() == str(prod_val).lower() else "mismatch"

        if status == "match":
            matched += 1
        details.append({"spec": spec, "status": status, "required": req_val, "product": prod_val})

    score = matched / len(specs)
    return {
        "product": product,
        "score": round(score, 3),
        "details": details,
    }


def _price_items(matches: List[Dict[str, Any]], tests: List[Dict[str, Any]]) -> Dict[str, Any]:
    materials = []
    total_material = 0.0

    for match in matches:
        item = match["item"]
        top = match["matches"][0]["product"]
        unit_price = top["unit_price"]
        line_total = unit_price * item["quantity"]
        total_material += line_total
        materials.append(
            {
                "item_id": item["item_id"],
                "description": item["description"],
                "sku": top["sku"],
                "quantity": item["quantity"],
                "unit_price": unit_price,
                "total": line_total,
            }
        )

    test_rows = []
    total_tests = 0.0
    # Use 1 test per item per type for the demo
    for t in tests:
        qty = len(matches)
        line_total = t["unit_price"] * qty
        total_tests += line_total
        test_rows.append(
            {
                "test_code": t["code"],
                "name": t["name"],
                "quantity": qty,
                "unit_price": t["unit_price"],
                "total": line_total,
            }
        )

    return {
        "materials": materials,
        "tests": test_rows,
        "totals": {
            "materials": total_material,
            "tests": total_tests,
            "grand_total": total_material + total_tests,
        },
    }


# ---------- Routes ----------
@router.get("/rfps")
async def list_rfps():
    """Return available demo RFPs."""
    return {"rfps": _mock_rfps()}


@router.post("/run")
async def run_demo_pipeline(rfp_id: Optional[str] = Query(None)):
    """Run the full demo pipeline for the selected RFP."""
    """Run the full demo pipeline for the selected RFP."""
    rfps = _mock_rfps()
    selected = next((r for r in rfps if r["id"] == rfp_id), rfps[0])

    items = _mock_items(selected["id"])
    products = _product_catalog()
    tests = _test_catalog()

    matches: List[Dict[str, Any]] = []
    for item in items:
        scored = [_score_product(item["requirements"], p) for p in products]
        top3 = sorted(scored, key=lambda s: s["score"], reverse=True)[:3]
        matches.append(
            {
                "item": item,
                "matches": top3,
                "best_score": top3[0]["score"] if top3 else 0,
            }
        )

    pricing = _price_items(matches, tests)

    response = {
        "rfp": selected,
        "items": items,
        "matches": matches,
        "pricing": pricing,
        "summary": {
            "time_to_complete_hours": 2,
            "avg_spec_match": round(sum(m["best_score"] for m in matches) / len(matches), 3),
            "completeness": "all_sections_covered",
        },
    }

    return response

