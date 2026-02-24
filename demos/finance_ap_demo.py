"""Finance AP Invoice Exception Triage Demo.

Run this script to see AgentFlow Framework in action with the
Finance Accounts Payable use case.

Usage:
    python demos/finance_ap_demo.py
    python demos/finance_ap_demo.py --scenario high_value
    python demos/finance_ap_demo.py --scenario duplicate
"""
import asyncio
import argparse
import json
from datetime import date

from agentflow.agents.supervisor import SupervisorAgent
from agentflow.tools.registry import registry
from agentflow.store.memory import memory_store
from agentflow.observability.logger import get_logger, configure_logging

configure_logging(log_level="INFO")
logger = get_logger(__name__)

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

# ---- Tool Registration for Demo -----------------------------------


def register_demo_tools():
    """Register finance-specific tools for the demo."""
    from agentflow.tools.base import AgentFlowTool
    from langchain.tools import tool

    @tool
    def validate_po_number(po_number: str) -> str:
        """Validate a PO number exists in the ERP system."""
        valid_pos = ["PO-2024-100", "PO-2024-200", "PO-2024-300"]
        if po_number in valid_pos:
            return f"PO {po_number} is VALID - approved budget available"
        elif not po_number:
            return "ERROR: Missing PO number - invoice cannot be processed without PO"
        else:
            return f"WARNING: PO {po_number} not found in ERP system"

    @tool
    def check_duplicate_invoice(invoice_id: str, vendor_name: str, amount: float) -> str:
        """Check if invoice is a duplicate in the payment system."""
        # Simulated duplicate check
        if "003" in invoice_id:
            return f"WARNING: Potential duplicate found for vendor {vendor_name} - similar invoice processed 14 days ago"
        return f"OK: No duplicate invoice found for {invoice_id}"

    @tool
    def get_vendor_risk_score(vendor_name: str) -> str:
        """Get vendor risk assessment from vendor management system."""
        risk_scores = {
            "Acme Supplies Co.": "LOW (score: 12/100) - Preferred vendor, 5yr relationship",
            "Global Tech Solutions": "MEDIUM (score: 45/100) - New vendor, 3 invoices",
            "Office Mart": "MEDIUM (score: 52/100) - Payment disputes in past",
            "Precision Parts Ltd.": "LOW (score: 18/100) - Established vendor, compliant",
        }
        return risk_scores.get(vendor_name, f"UNKNOWN: Vendor {vendor_name} not in system")

    @tool
    def update_erp_invoice_status(invoice_id: str, status: str, notes: str) -> str:
        """Update invoice status in the ERP system."""
        logger.info("erp_update", invoice_id=invoice_id, status=status)
        return f"ERP UPDATED: Invoice {invoice_id} status set to {status}. Notes: {notes}"

    registry.register(validate_po_number)
    registry.register(check_duplicate_invoice)
    registry.register(get_vendor_risk_score)
    registry.register(update_erp_invoice_status)
    logger.info("demo_tools_registered", count=4)


async def run_triage(scenario_data: dict) -> None:
    """Run the invoice triage workflow for a given scenario."""
    print("\n" + "=" * 70)
    print(f"AGENTFLOW FRAMEWORK - Finance AP Invoice Triage Demo")
    print("=" * 70)
    print(f"Scenario  : {scenario_data['description']}")
    print(f"Invoice ID: {scenario_data['invoice_id']}")
    print(f"Vendor    : {scenario_data['vendor_name']}")
    print(f"Amount    : ${scenario_data['invoice_amount']:,.2f}")
    print(f"PO Number : {scenario_data['po_number'] or 'MISSING'}")
    print("-" * 70)

    task = (
        f"Process Finance AP invoice triage for invoice {scenario_data['invoice_id']} "
        f"from vendor {scenario_data['vendor_name']} for amount "
        f"${scenario_data['invoice_amount']:,.2f}. PO number: "
        f"{scenario_data['po_number'] or 'NOT PROVIDED'}. Invoice date: "
        f"{scenario_data['invoice_date']}. "
        f"Use the available tools to: 1) validate the PO number, "
        f"2) check for duplicate invoices, 3) assess vendor risk score, "
        f"4) classify the exception type and priority, "
        f"5) recommend approval routing, and "
        f"6) update ERP with triage decision. "
        f"Provide a structured triage report."
    )

    agent = SupervisorAgent(
        tool_names=[
            "validate_po_number",
            "check_duplicate_invoice",
            "get_vendor_risk_score",
            "update_erp_invoice_status",
        ]
    )

    print("\nRunning AI Triage...")
    result = await agent.run(task)

    print("\nTRIAGE RESULT:")
    print("-" * 70)
    print(result)
    print("=" * 70)

    # Store result in memory
    memory_store.set(f"triage_{scenario_data['invoice_id']}", result)


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

    # Register demo tools
    register_demo_tools()

    if args.all:
        for name, scenario in SCENARIOS.items():
            print(f"\n>>> Running scenario: {name}")
            asyncio.run(run_triage(scenario))
    else:
        scenario = SCENARIOS[args.scenario]
        asyncio.run(run_triage(scenario))


if __name__ == "__main__":
    main()
