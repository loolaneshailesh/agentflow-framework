"""Finance AP Invoice Exception Triage Demo.

Run this script to see AgentFlow Framework in action with the
Finance Accounts Payable use case.

Usage:
    python demos/finance_ap_demo.py
    python demos/finance_ap_demo.py --scenario high_value
    python demos/finance_ap_demo.py --scenario duplicate
    python demos/finance_ap_demo.py --all
"""
import asyncio
import argparse
from datetime import date

from agentflow.agents.supervisor import SupervisorAgent
from agentflow.tools.registry import get_registry
from agentflow.core.logger import configure_logging, get_logger

configure_logging(level="INFO")
logger = get_logger(__name__)

registry = get_registry()

# Simple in-memory store (replaces agentflow.store.memory)
_memory: dict = {}

class _MemoryStore:
    def set(self, key, value):
        _memory[key] = value
    def get(self, key, default=None):
        return _memory.get(key, default)

memory_store = _MemoryStore()

# ---- Demo Scenarios ------------------------------------------------

SCENARIOS = {
    "normal": {
        "invoice_id": "INV-2024-001",
        "vendor_name": "Acme Supplies Co.",
        "invoice_amount": 4500.00,
        "po_number": "PO-2024-100",
        "invoice_date": str(date.today()),
        "description": "Standard low-value invoice - should auto-approve",
    },
    "high_value": {
        "invoice_id": "INV-2024-002",
        "vendor_name": "Global Tech Solutions",
        "invoice_amount": 125000.00,
        "po_number": "PO-2024-200",
        "invoice_date": str(date.today()),
        "description": "High-value invoice - requires Finance Manager approval",
    },
    "duplicate": {
        "invoice_id": "INV-2024-003",
        "vendor_name": "Office Mart",
        "invoice_amount": 8750.00,
        "po_number": "",
        "invoice_date": str(date.today()),
        "description": "Missing PO + possible duplicate - requires investigation",
    },
    "amount_mismatch": {
        "invoice_id": "INV-2024-004",
        "vendor_name": "Precision Parts Ltd.",
        "invoice_amount": 35000.00,
        "po_number": "PO-2024-300",
        "invoice_date": str(date.today()),
        "description": "Amount 40% above PO value - requires AP Supervisor review",
    },
}

# ---- Tool Registration ---------------------------------------------

def validate_po_number(po_number: str) -> str:
    """Validate a PO number exists in the ERP system."""
    valid_pos = ["PO-2024-100", "PO-2024-200", "PO-2024-300"]
    if po_number in valid_pos:
        return f"PO {po_number} is VALID - approved budget available"
    elif not po_number:
        return "ERROR: Missing PO number - invoice cannot be processed without PO"
    else:
        return f"WARNING: PO {po_number} not found in ERP system"


def check_duplicate_invoice(invoice_id: str, vendor_name: str = "", amount: float = 0) -> str:
    """Check if invoice is a duplicate in the payment system."""
    if "003" in invoice_id:
        return f"WARNING: Potential duplicate found for vendor {vendor_name} - similar invoice processed 14 days ago"
    return f"OK: No duplicate invoice found for {invoice_id}"


def get_vendor_risk_score(vendor_name: str) -> str:
    """Get vendor risk assessment from vendor management system."""
    risk_scores = {
        "Acme Supplies Co.":    "LOW (score: 12/100) - Preferred vendor, 5yr relationship",
        "Global Tech Solutions":"MEDIUM (score: 45/100) - New vendor, 3 invoices",
        "Office Mart":          "MEDIUM (score: 52/100) - Payment disputes in past",
        "Precision Parts Ltd.": "LOW (score: 18/100) - Established vendor, compliant",
    }
    return risk_scores.get(vendor_name, f"UNKNOWN: Vendor {vendor_name} not in system")


def update_erp_invoice_status(invoice_id: str, status: str = "TRIAGED", notes: str = "") -> str:
    """Update invoice status in the ERP system."""
    logger.info(f"ERP update: invoice={invoice_id} status={status}")
    return f"ERP UPDATED: Invoice {invoice_id} status set to {status}. Notes: {notes}"


def register_demo_tools():
    """Register finance-specific tools for the demo."""
    registry.register(validate_po_number,          name="validate_po_number")
    registry.register(check_duplicate_invoice,     name="check_duplicate_invoice")
    registry.register(get_vendor_risk_score,       name="get_vendor_risk_score")
    registry.register(update_erp_invoice_status,   name="update_erp_invoice_status")
    logger.info("Demo tools registered: 4 tools")


# ---- Triage Logic --------------------------------------------------

def run_triage(scenario_data: dict) -> None:
    """Run the invoice triage workflow for a given scenario."""
    print("\n" + "=" * 70)
    print("AGENTFLOW FRAMEWORK - Finance AP Invoice Triage Demo")
    print("=" * 70)
    print(f"Scenario  : {scenario_data['description']}")
    print(f"Invoice ID: {scenario_data['invoice_id']}")
    print(f"Vendor    : {scenario_data['vendor_name']}")
    print(f"Amount    : ${scenario_data['invoice_amount']:,.2f}")
    print(f"PO Number : {scenario_data['po_number'] or 'MISSING'}")
    print("-" * 70)

    invoice_id  = scenario_data["invoice_id"]
    vendor      = scenario_data["vendor_name"]
    amount      = scenario_data["invoice_amount"]
    po_number   = scenario_data["po_number"]

    print("\nRunning Triage Tools...")

    # Step 1 - Validate PO
    po_result = registry.invoke("validate_po_number", {"po_number": po_number})
    print(f"  [PO Check]       {po_result}")

    # Step 2 - Duplicate check
    dup_result = registry.invoke("check_duplicate_invoice", {
        "invoice_id": invoice_id,
        "vendor_name": vendor,
        "amount": amount
    })
    print(f"  [Duplicate]      {dup_result}")

    # Step 3 - Vendor risk
    risk_result = registry.invoke("get_vendor_risk_score", vendor)
    print(f"  [Vendor Risk]    {risk_result}")

    # Step 4 - Routing decision
    if amount >= 100000:
        routing = "ESCALATE  Finance Director approval required"
        priority = "CRITICAL"
    elif amount >= 10000 or "WARNING" in po_result or "WARNING" in dup_result:
        routing = "ESCALATE  Finance Manager approval required"
        priority = "HIGH"
    elif "ERROR" in po_result:
        routing = "HOLD  Missing PO, return to vendor"
        priority = "HIGH"
    else:
        routing = "AUTO-APPROVE  Within policy limits"
        priority = "LOW"

    # Step 5 - Update ERP
    erp_result = registry.invoke("update_erp_invoice_status", {
        "invoice_id": invoice_id,
        "status": priority,
        "notes": routing
    })
    print(f"  [ERP Update]     {erp_result}")

    # Step 6 - Final report
    result = {
        "invoice_id":   invoice_id,
        "vendor":       vendor,
        "amount":       amount,
        "po_check":     po_result,
        "duplicate":    dup_result,
        "vendor_risk":  risk_result,
        "priority":     priority,
        "routing":      routing,
    }

    print("\nTRIAGE RESULT:")
    print("-" * 70)
    for k, v in result.items():
        print(f"  {k:<15}: {v}")
    print("=" * 70)

    # Store in memory
    memory_store.set(f"triage_{invoice_id}", result)


def main():
    parser = argparse.ArgumentParser(description="Finance AP Invoice Triage Demo")
    parser.add_argument(
        "--scenario",
        choices=list(SCENARIOS.keys()),
        default="normal",
        help="Demo scenario to run",
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Run all demo scenarios",
    )
    args = parser.parse_args()

    register_demo_tools()

    if args.all:
        for name, scenario in SCENARIOS.items():
            print(f"\n>>> Running scenario: {name}")
            run_triage(scenario)
    else:
        scenario = SCENARIOS[args.scenario]
        run_triage(scenario)


if __name__ == "__main__":
    main()
