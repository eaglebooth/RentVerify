"use client";

import { motion } from "framer-motion";
import {
  ArrowRight,
  BadgeDollarSign,
  Camera,
  CheckCircle2,
  ClipboardCheck,
  DoorOpen,
  FileImage,
  FileText,
  Gauge,
  Home as HomeIcon,
  KeyRound,
  Link2,
  ReceiptText,
  Scale,
  ShieldCheck,
  Sparkles,
  Wallet,
} from "lucide-react";
import { useMemo, useState } from "react";
import { connectWallet, readContract, writeContract } from "@/lib/genlayer";

type CaseDraft = {
  property: string;
  landlord: string;
  tenant: string;
  deposit: string;
  leaseUrl: string;
  moveinUrl: string;
  checkoutUrl: string;
  landlordClaimUrl: string;
  tenantStatementUrl: string;
  caseId: string;
};

const defaultCase: CaseDraft = {
  property: "Unit 8B, Ember Court",
  landlord: "0x00000000000000000000000000000000000000A1",
  tenant: "0x00000000000000000000000000000000000000B2",
  deposit: "1200",
  leaseUrl: "https://example.com/rentverify/lease-unit-8b",
  moveinUrl: "https://example.com/rentverify/move-in-gallery",
  checkoutUrl: "https://example.com/rentverify/check-out-gallery",
  landlordClaimUrl: "https://example.com/rentverify/landlord-claim",
  tenantStatementUrl: "https://example.com/rentverify/tenant-statement",
  caseId: "0",
};

const evidenceCards = [
  {
    key: "leaseUrl",
    label: "Lease packet",
    icon: FileText,
    copy: "Rules, inventory, signed baseline.",
  },
  {
    key: "moveinUrl",
    label: "Move-in lock",
    icon: Camera,
    copy: "Photos/video frozen at signing.",
  },
  {
    key: "checkoutUrl",
    label: "Checkout reel",
    icon: FileImage,
    copy: "Move-out condition evidence.",
  },
  {
    key: "landlordClaimUrl",
    label: "Owner claim",
    icon: ReceiptText,
    copy: "Repair quote and disputed items.",
  },
  {
    key: "tenantStatementUrl",
    label: "Renter reply",
    icon: ClipboardCheck,
    copy: "Tenant context and objections.",
  },
] as const;

function shortAddress(value: unknown) {
  const text = String(value || "");
  if (text.length < 12) return text;
  return `${text.slice(0, 6)}...${text.slice(-4)}`;
}

function parseJsonRecord(value: unknown) {
  try {
    return JSON.parse(String(value)) as Record<string, string>;
  } catch {
    return {};
  }
}

export default function Home() {
  const [draft, setDraft] = useState<CaseDraft>(defaultCase);
  const [wallet, setWallet] = useState("");
  const [busy, setBusy] = useState(false);
  const [status, setStatus] = useState("Ready. Deploy RentVerify, then set NEXT_PUBLIC_CONTRACT_ADDRESS.");
  const [decision, setDecision] = useState({
    status: "No decision yet",
    decision: "PENDING",
    refund: "0",
    deduction: "0",
    damage: "0",
    wear: "0",
    reason: "The GenLayer jury memo appears after adjudication.",
  });
  const [stats, setStats] = useState({
    caseCount: "0",
    escrowTotal: "0",
    releasedTotal: "0",
    tenantRefunded: "0",
    landlordAwarded: "0",
  });

  const configured = useMemo(() => Boolean(process.env.NEXT_PUBLIC_CONTRACT_ADDRESS), []);

  function setField(key: keyof CaseDraft, value: string) {
    setDraft((current) => ({ ...current, [key]: value }));
  }

  async function handleConnect() {
    const result = await connectWallet();
    if (result.success) {
      const account = String(result.data);
      setWallet(account);
      setStatus(`Wallet connected: ${shortAddress(account)}`);
    } else {
      setStatus(result.error || "Wallet connection failed");
    }
  }

  async function refreshStats() {
    const result = await readContract("get_escrow_stats");
    if (!result.success) {
      setStatus(result.error || "Escrow stats unavailable");
      return;
    }
    const parsed = parseJsonRecord(result.data);
    setStats({
      caseCount: parsed.case_count || "0",
      escrowTotal: parsed.escrow_total || "0",
      releasedTotal: parsed.released_total || "0",
      tenantRefunded: parsed.tenant_refunded_total || "0",
      landlordAwarded: parsed.landlord_awarded_total || "0",
    });
    setStatus("Escrow stats refreshed from contract.");
  }

  async function readDecision() {
    const result = await readContract("get_decision", [BigInt(draft.caseId || "0")]);
    if (!result.success) {
      setStatus(result.error || "Decision unavailable");
      return;
    }
    const parsed = parseJsonRecord(result.data);
    const report = parseJsonRecord(parsed.ai_report || "{}");
    setDecision({
      status: parsed.status || "UNKNOWN",
      decision: parsed.decision || "PENDING",
      refund: parsed.refund_amount || "0",
      deduction: parsed.deduction_amount || "0",
      damage: parsed.damage_score || "0",
      wear: parsed.wear_score || "0",
      reason: report.reason || parsed.ai_report || "No AI memo stored yet.",
    });
    setStatus("Decision refreshed from contract.");
  }

  async function openCase() {
    setBusy(true);
    setStatus("Opening deposit escrow case...");
    const result = await writeContract("open_case", [
      draft.property,
      draft.landlord,
      draft.tenant,
      BigInt(draft.deposit || "0"),
      draft.leaseUrl,
      draft.moveinUrl,
    ]);
    setBusy(false);
    if (result.success) {
      setStatus(`Case opened. Tx ${shortAddress(result.hash)}`);
      await refreshStats();
    } else {
      setStatus(result.error || "Open case failed");
    }
  }

  async function submitCheckout() {
    setBusy(true);
    setStatus("Submitting checkout evidence...");
    const result = await writeContract("submit_checkout", [
      BigInt(draft.caseId || "0"),
      draft.checkoutUrl,
      draft.landlordClaimUrl,
      draft.tenantStatementUrl,
    ]);
    setBusy(false);
    setStatus(result.success ? `Checkout submitted. Tx ${shortAddress(result.hash)}` : result.error || "Submit checkout failed");
  }

  async function adjudicate() {
    setBusy(true);
    setStatus("Running GenLayer deposit jury...");
    const result = await writeContract("adjudicate", [BigInt(draft.caseId || "0")]);
    setBusy(false);
    if (result.success) {
      setStatus(`AI decision finalized: ${String(result.data || result.status || "DECIDED")}`);
      await readDecision();
    } else {
      setStatus(result.error || "Adjudication failed");
    }
  }

  async function releaseDeposit() {
    setBusy(true);
    setStatus("Releasing escrow ledger...");
    const result = await writeContract("release_deposit", [BigInt(draft.caseId || "0")]);
    setBusy(false);
    if (result.success) {
      setStatus(`Deposit released. Tx ${shortAddress(result.hash)}`);
      await refreshStats();
      await readDecision();
    } else {
      setStatus(result.error || "Release failed");
    }
  }

  return (
    <main className="page">
      <nav className="nav">
        <a className="brand" href="#top">
          <span><KeyRound size={22} /></span>
          RentVerify
        </a>
        <div className="nav-links">
          <a href="#handoff">Handoff</a>
          <a href="#evidence">Evidence</a>
          <a href="#decision">Decision</a>
        </div>
        <button className="ghost-button" type="button" onClick={handleConnect}>
          <Wallet size={18} />
          {wallet ? shortAddress(wallet) : "Connect wallet"}
        </button>
      </nav>

      <section className="hero" id="top">
        <motion.div className="hero-copy" initial={{ opacity: 0, y: 28 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.7 }}>
          <span className="eyebrow"><Sparkles size={16} /> GenLayer deposit escrow</span>
          <h1>Stop unfair deposit grabs at checkout.</h1>
          <p>
            RentVerify locks move-in evidence, compares it against checkout photos and claims,
            then lets a GenLayer AI jury decide a fair refund and repair deduction on-chain.
          </p>
          <div className="hero-actions">
            <a className="primary-button" href="#handoff">Open handoff desk <ArrowRight size={18} /></a>
            <button className="ghost-button" type="button" onClick={refreshStats}>Refresh escrow <Gauge size={18} /></button>
          </div>
        </motion.div>

        <motion.div className="deposit-card" initial={{ opacity: 0, rotate: 2, y: 24 }} animate={{ opacity: 1, rotate: 0, y: 0 }} transition={{ duration: 0.7, delay: 0.1 }}>
          <div className="deposit-top">
            <span>Escrow packet</span>
            <HomeIcon size={22} />
          </div>
          <div className="deposit-amount">${draft.deposit}</div>
          <div className="deposit-addresses">
            <div><small>Landlord</small><strong>{shortAddress(draft.landlord)}</strong></div>
            <div><small>Tenant</small><strong>{shortAddress(draft.tenant)}</strong></div>
          </div>
          <div className="refund-meter">
            <div style={{ width: "82%" }} />
          </div>
          <p>Escrow should move by evidence, not leverage. The contract stores a neutral payout ledger after AI review.</p>
        </motion.div>
      </section>

      <section className="section" id="handoff">
        <div className="section-title">
          <span>01 / Handoff desk</span>
          <h2>One case card, not a boring form.</h2>
        </div>
        <div className="handoff-board">
          <div className="apartment-card">
            <DoorOpen size={34} />
            <label>Rental unit</label>
            <input value={draft.property} onChange={(event) => setField("property", event.target.value)} />
          </div>
          <div className="party-strip">
            <div>
              <small>Owner wallet</small>
              <input value={draft.landlord} onChange={(event) => setField("landlord", event.target.value)} />
            </div>
            <div>
              <small>Renter wallet</small>
              <input value={draft.tenant} onChange={(event) => setField("tenant", event.target.value)} />
            </div>
            <div>
              <small>Deposit locked</small>
              <input value={draft.deposit} onChange={(event) => setField("deposit", event.target.value)} />
            </div>
          </div>
          <button className="primary-button large" type="button" disabled={busy} onClick={openCase}>
            Lock move-in packet <ShieldCheck size={18} />
          </button>
        </div>
      </section>

      <section className="section evidence-section" id="evidence">
        <div className="section-title">
          <span>02 / Evidence reel</span>
          <h2>Five links become one fair comparison.</h2>
        </div>
        <div className="evidence-reel">
          {evidenceCards.map((card, index) => {
            const Icon = card.icon;
            return (
              <article className="evidence-card" key={card.key}>
                <div className="evidence-number">{String(index + 1).padStart(2, "0")}</div>
                <Icon size={26} />
                <h3>{card.label}</h3>
                <p>{card.copy}</p>
                <div className="link-pill">
                  <Link2 size={15} />
                  <input
                    value={draft[card.key]}
                    onChange={(event) => setField(card.key, event.target.value)}
                    aria-label={card.label}
                  />
                </div>
              </article>
            );
          })}
        </div>
        <div className="case-toolbar">
          <label>
            Case ID
            <input value={draft.caseId} onChange={(event) => setField("caseId", event.target.value)} />
          </label>
          <button className="dark-button" type="button" disabled={busy} onClick={submitCheckout}>Submit checkout <Camera size={18} /></button>
          <button className="primary-button" type="button" disabled={busy} onClick={adjudicate}>Run AI review <Scale size={18} /></button>
        </div>
        <div className="inline-status">
          <span>{busy ? "Working" : "Latest status"}</span>
          <p>{status}</p>
        </div>
      </section>

      <section className="section decision-grid" id="decision">
        <div className="decision-panel">
          <span className="panel-kicker">03 / On-chain decision</span>
          <h2>{decision.decision}</h2>
          <p>{decision.reason}</p>
          <div className="payout-split">
            <div>
              <small>Refund to tenant</small>
              <strong>${decision.refund}</strong>
            </div>
            <div>
              <small>Deduction to landlord</small>
              <strong>${decision.deduction}</strong>
            </div>
          </div>
          <div className="score-lanes">
            <div><span>Damage signal</span><div><i style={{ width: `${decision.damage}%` }} /></div></div>
            <div><span>Wear signal</span><div><i style={{ width: `${decision.wear}%` }} /></div></div>
          </div>
          <div className="decision-actions">
            <button className="ghost-button" type="button" onClick={readDecision}>Read decision <CheckCircle2 size={18} /></button>
            <button className="primary-button" type="button" disabled={busy} onClick={releaseDeposit}>Release deposit <BadgeDollarSign size={18} /></button>
          </div>
        </div>

        <aside className="ledger-panel">
          <h3>Escrow ledger</h3>
          <div><span>Cases</span><strong>{stats.caseCount}</strong></div>
          <div><span>Total escrow</span><strong>${stats.escrowTotal}</strong></div>
          <div><span>Released</span><strong>${stats.releasedTotal}</strong></div>
          <div><span>Tenant refunded</span><strong>${stats.tenantRefunded}</strong></div>
          <div><span>Landlord awarded</span><strong>${stats.landlordAwarded}</strong></div>
          <div className="status-box">
            <strong>{configured ? "Contract configured" : "Contract address pending"}</strong>
            <p>{status}</p>
          </div>
        </aside>
      </section>
    </main>
  );
}
