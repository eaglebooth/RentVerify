# v0.2.16
# { "Depends": "py-genlayer:1jb45aa8ynh2a9c9xn3b7qqh8sm5q93hwfp7jqmwsfhh8jpz09h6" }
from genlayer import *
import typing
import json


class RentVerify(gl.Contract):
    case_count: u256
    case_property: TreeMap[u256, str]
    case_landlord_wallet: TreeMap[u256, str]
    case_tenant_wallet: TreeMap[u256, str]
    case_deposit_amount: TreeMap[u256, u256]
    case_lease_url: TreeMap[u256, str]
    case_movein_url: TreeMap[u256, str]
    case_checkout_url: TreeMap[u256, str]
    case_landlord_claim_url: TreeMap[u256, str]
    case_tenant_statement_url: TreeMap[u256, str]
    case_status: TreeMap[u256, str]

    case_decision: TreeMap[u256, str]
    case_deduction_amount: TreeMap[u256, u256]
    case_refund_amount: TreeMap[u256, u256]
    case_damage_score: TreeMap[u256, u256]
    case_wear_score: TreeMap[u256, u256]
    case_ai_report: TreeMap[u256, str]

    escrow_total: u256
    released_total: u256
    landlord_awarded_total: u256
    tenant_refunded_total: u256

    def __init__(self):
        self.case_count = u256(0)
        self.escrow_total = u256(0)
        self.released_total = u256(0)
        self.landlord_awarded_total = u256(0)
        self.tenant_refunded_total = u256(0)

    def is_url(self, value: str) -> u256:
        if len(value) >= 4 and value[:4] == "http":
            return u256(1)
        return u256(0)

    def truncate(self, value: str, limit: u256) -> str:
        if len(value) > int(limit):
            return value[: int(limit)] + "...[TRUNCATED]"
        return value

    def clamp_score(self, value: typing.Any) -> u256:
        parsed = int(value)
        if parsed < 0:
            return u256(0)
        if parsed > 100:
            return u256(100)
        return u256(parsed)

    @gl.public.write
    def open_case(
        self,
        property_label: str,
        landlord_wallet: str,
        tenant_wallet: str,
        deposit_amount: u256,
        lease_url: str,
        movein_url: str,
    ) -> typing.Any:
        if len(property_label) == 0:
            return "INVALID_PROPERTY"
        if len(landlord_wallet) == 0:
            return "INVALID_LANDLORD"
        if len(tenant_wallet) == 0:
            return "INVALID_TENANT"
        if landlord_wallet == tenant_wallet:
            return "PARTIES_MUST_DIFFER"
        if deposit_amount == u256(0):
            return "INVALID_DEPOSIT"
        if self.is_url(lease_url) == u256(0):
            return "INVALID_LEASE_URL"
        if self.is_url(movein_url) == u256(0):
            return "INVALID_MOVEIN_URL"

        case_id = self.case_count
        self.case_property[case_id] = property_label
        self.case_landlord_wallet[case_id] = landlord_wallet
        self.case_tenant_wallet[case_id] = tenant_wallet
        self.case_deposit_amount[case_id] = deposit_amount
        self.case_lease_url[case_id] = lease_url
        self.case_movein_url[case_id] = movein_url
        self.case_checkout_url[case_id] = ""
        self.case_landlord_claim_url[case_id] = ""
        self.case_tenant_statement_url[case_id] = ""
        self.case_status[case_id] = "ACTIVE"
        self.case_decision[case_id] = ""
        self.case_deduction_amount[case_id] = u256(0)
        self.case_refund_amount[case_id] = u256(0)
        self.case_damage_score[case_id] = u256(0)
        self.case_wear_score[case_id] = u256(0)
        self.case_ai_report[case_id] = ""
        self.escrow_total = self.escrow_total + deposit_amount
        self.case_count = case_id + u256(1)
        return case_id

    @gl.public.write
    def submit_checkout(
        self,
        case_id: u256,
        checkout_url: str,
        landlord_claim_url: str,
        tenant_statement_url: str,
    ) -> str:
        if case_id >= self.case_count:
            return "INVALID_CASE_ID"
        if self.case_status[case_id] != "ACTIVE":
            return "INVALID_STATUS"
        if self.is_url(checkout_url) == u256(0):
            return "INVALID_CHECKOUT_URL"
        if self.is_url(landlord_claim_url) == u256(0):
            return "INVALID_LANDLORD_CLAIM_URL"
        if self.is_url(tenant_statement_url) == u256(0):
            return "INVALID_TENANT_STATEMENT_URL"

        self.case_checkout_url[case_id] = checkout_url
        self.case_landlord_claim_url[case_id] = landlord_claim_url
        self.case_tenant_statement_url[case_id] = tenant_statement_url
        self.case_status[case_id] = "CHECKOUT_SUBMITTED"
        return "CHECKOUT_SUBMITTED"

    @gl.public.write
    def adjudicate(self, case_id: u256) -> str:
        if case_id >= self.case_count:
            return "INVALID_CASE_ID"
        if self.case_status[case_id] != "CHECKOUT_SUBMITTED":
            return "EVIDENCE_NOT_READY"

        property_label = self.case_property[case_id]
        deposit_amount = self.case_deposit_amount[case_id]
        lease_url = self.case_lease_url[case_id]
        movein_url = self.case_movein_url[case_id]
        checkout_url = self.case_checkout_url[case_id]
        landlord_claim_url = self.case_landlord_claim_url[case_id]
        tenant_statement_url = self.case_tenant_statement_url[case_id]

        def run_review() -> str:
            try:
                lease_resp = gl.nondet.web.render(lease_url, media_type="html")
                movein_resp = gl.nondet.web.render(movein_url, media_type="html")
                checkout_resp = gl.nondet.web.render(checkout_url, media_type="html")
                claim_resp = gl.nondet.web.render(landlord_claim_url, media_type="html")
                tenant_resp = gl.nondet.web.render(tenant_statement_url, media_type="html")
                lease = self.truncate(lease_resp.body.decode("utf-8"), u256(1100))
                movein = self.truncate(movein_resp.body.decode("utf-8"), u256(1600))
                checkout = self.truncate(checkout_resp.body.decode("utf-8"), u256(1600))
                landlord_claim = self.truncate(claim_resp.body.decode("utf-8"), u256(1300))
                tenant_statement = self.truncate(tenant_resp.body.decode("utf-8"), u256(1300))
            except Exception:
                return json.dumps({"error": "WEB_RENDER_FAILED"}, sort_keys=True, separators=(",", ":"))

            prompt = f"""
You are RentVerify, a neutral GenLayer rental deposit adjudication jury.

PROPERTY: {property_label}
ESCROWED DEPOSIT: {deposit_amount}

LEASE / MOVE-IN RULES:
{lease}

LOCKED MOVE-IN CONDITION EVIDENCE:
{movein}

MOVE-OUT / CHECKOUT CONDITION EVIDENCE:
{checkout}

LANDLORD CLAIM:
{landlord_claim}

TENANT STATEMENT:
{tenant_statement}

TASK:
Compare move-in evidence with checkout evidence. Decide whether claimed damage is
ordinary wear and tear, pre-existing condition, tenant-caused damage, or unverifiable.
Protect tenants from unfair full-deposit capture, while allowing reasonable repair
deductions for real tenant-caused damage.

SCORING:
- damage_score 0-100: strength that checkout damage is tenant-caused damage.
- wear_score 0-100: strength that condition is ordinary wear, aging, cleaning, or pre-existing.
- evidence_confidence 0-100: quality and consistency of evidence.

DEDUCTION RULES:
- FULL_REFUND: deduction_amount must be 0.
- PARTIAL_DEDUCTION: deduction_amount must be a conservative whole number below deposit.
- LANDLORD_CLAIM: only if evidence strongly supports major tenant-caused damage.
- NEEDS_REVIEW: use when evidence is unclear; deduction_amount must be 0.
- deduction_amount must never exceed {deposit_amount}.
- refund_amount must equal deposit minus deduction.

Respond with ONLY strict JSON:
{{
  "decision": "FULL_REFUND" | "PARTIAL_DEDUCTION" | "LANDLORD_CLAIM" | "NEEDS_REVIEW",
  "damage_score": 0,
  "wear_score": 0,
  "evidence_confidence": 0,
  "deduction_amount": 0,
  "refund_amount": 0,
  "reason": "one concise sentence explaining the fair deposit outcome"
}}
"""
            return gl.nondet.exec_prompt(prompt)

        consensus = gl.eq_principle.strict_eq(run_review)
        try:
            data = json.loads(consensus)
        except json.JSONDecodeError:
            return "INVALID_AI_RESPONSE"

        if "error" in data:
            return "WEB_RENDER_FAILED"

        decision = str(data.get("decision", "")).upper()
        if decision not in ["FULL_REFUND", "PARTIAL_DEDUCTION", "LANDLORD_CLAIM", "NEEDS_REVIEW"]:
            return "INVALID_DECISION"

        deduction = u256(int(data.get("deduction_amount", 0)))
        refund = u256(int(data.get("refund_amount", 0)))
        damage_score = self.clamp_score(data.get("damage_score", 0))
        wear_score = self.clamp_score(data.get("wear_score", 0))

        if deduction > deposit_amount:
            deduction = deposit_amount
        expected_refund = deposit_amount - deduction
        if refund != expected_refund:
            refund = expected_refund
        if decision == "FULL_REFUND" or decision == "NEEDS_REVIEW":
            deduction = u256(0)
            refund = deposit_amount
        if decision == "LANDLORD_CLAIM" and damage_score < u256(75):
            return "AI_DECISION_INCONSISTENT"
        if decision == "PARTIAL_DEDUCTION" and deduction == u256(0):
            return "AI_DECISION_INCONSISTENT"

        self.case_decision[case_id] = decision
        self.case_deduction_amount[case_id] = deduction
        self.case_refund_amount[case_id] = refund
        self.case_damage_score[case_id] = damage_score
        self.case_wear_score[case_id] = wear_score
        self.case_ai_report[case_id] = consensus
        self.case_status[case_id] = "DECIDED"
        return decision

    @gl.public.write
    def release_deposit(self, case_id: u256) -> str:
        if case_id >= self.case_count:
            return "INVALID_CASE_ID"
        if self.case_status[case_id] != "DECIDED":
            return "NOT_DECIDED"

        deposit = self.case_deposit_amount[case_id]
        deduction = self.case_deduction_amount[case_id]
        refund = self.case_refund_amount[case_id]
        if deduction + refund != deposit:
            return "PAYOUT_MISMATCH"

        self.released_total = self.released_total + deposit
        self.landlord_awarded_total = self.landlord_awarded_total + deduction
        self.tenant_refunded_total = self.tenant_refunded_total + refund
        self.case_status[case_id] = "RELEASED"
        return "RELEASED"

    @gl.public.view
    def get_case_count(self) -> u256:
        return self.case_count

    @gl.public.view
    def get_escrow_stats(self) -> str:
        data = {
            "case_count": str(self.case_count),
            "escrow_total": str(self.escrow_total),
            "landlord_awarded_total": str(self.landlord_awarded_total),
            "released_total": str(self.released_total),
            "tenant_refunded_total": str(self.tenant_refunded_total),
        }
        return json.dumps(data, sort_keys=True, separators=(",", ":"))

    @gl.public.view
    def get_case(self, case_id: u256) -> str:
        if case_id >= self.case_count:
            return json.dumps({"error": "INVALID_CASE_ID"}, sort_keys=True, separators=(",", ":"))
        data = {
            "checkout_url": self.case_checkout_url[case_id],
            "decision": self.case_decision[case_id],
            "deduction_amount": str(self.case_deduction_amount[case_id]),
            "deposit_amount": str(self.case_deposit_amount[case_id]),
            "landlord_claim_url": self.case_landlord_claim_url[case_id],
            "landlord_wallet": self.case_landlord_wallet[case_id],
            "lease_url": self.case_lease_url[case_id],
            "movein_url": self.case_movein_url[case_id],
            "property": self.case_property[case_id],
            "refund_amount": str(self.case_refund_amount[case_id]),
            "status": self.case_status[case_id],
            "tenant_statement_url": self.case_tenant_statement_url[case_id],
            "tenant_wallet": self.case_tenant_wallet[case_id],
        }
        return json.dumps(data, sort_keys=True, separators=(",", ":"))

    @gl.public.view
    def get_decision(self, case_id: u256) -> str:
        if case_id >= self.case_count:
            return json.dumps({"error": "INVALID_CASE_ID"}, sort_keys=True, separators=(",", ":"))
        data = {
            "ai_report": self.case_ai_report[case_id],
            "damage_score": str(self.case_damage_score[case_id]),
            "decision": self.case_decision[case_id],
            "deduction_amount": str(self.case_deduction_amount[case_id]),
            "refund_amount": str(self.case_refund_amount[case_id]),
            "status": self.case_status[case_id],
            "wear_score": str(self.case_wear_score[case_id]),
        }
        return json.dumps(data, sort_keys=True, separators=(",", ":"))
