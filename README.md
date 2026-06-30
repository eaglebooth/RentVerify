# RentVerify

RentVerify is a GenLayer rental deposit escrow dApp that adjudicates move-out disputes using locked move-in evidence, checkout evidence, landlord claims, and tenant statements.

**One-line pitch:** RentVerify dies without GenLayer because fair deposit refunds require subjective comparison of live evidence, AI reasoning, and an on-chain payout decision that neither landlord nor tenant should control alone.

## Why GenLayer

Traditional rental deposits are easy to abuse: a landlord can claim ordinary wear or minor cleaning issues justify taking an entire deposit. A normal smart contract can hold escrow, but it cannot judge whether a scratch, stain, or wall mark is normal wear and tear or tenant-caused damage.

RentVerify uses a GenLayer Intelligent Contract to:

- Lock lease and move-in evidence when the case is opened.
- Accept move-out evidence plus both party statements.
- Read the evidence through `gl.nondet.web.render`.
- Run an AI jury through `gl.nondet.exec_prompt`.
- Decide a fair deduction and refund.
- Release escrow according to the on-chain decision.

## Deployed Contract

```text
0x74dA23cFB560c531F00DF87e58f2746c0D078C8C
```

## Project Structure

```text
RentVerify/
  contracts/
    RentVerify.py
  frontend/
    src/app/page.tsx
    src/lib/genlayer.ts
  scripts/deploy/deploy.ps1
  tests/test_contract_static.py
```

## Contract Flow

1. Open a rental escrow case with property, parties, deposit, lease URL, and move-in evidence URL.
2. Submit checkout evidence, landlord claim, and tenant statement.
3. Run GenLayer AI adjudication.
4. Store decision, deduction, refund, damage score, wear score, and reason.
5. Release deposit ledger state.

## Pre-Deploy Verification

```powershell
python -m unittest discover -s tests
python -c "import ast; ast.parse(open('contracts/RentVerify.py', encoding='utf-8').read())"
genlayer lint contracts/RentVerify.py
```

## Frontend Setup

```powershell
cd frontend
npm install
copy .env.example .env.local
npm run dev -- -p 3040
```

Set the deployed contract address:

```text
NEXT_PUBLIC_CONTRACT_ADDRESS=<deployed-rentverify-address>
NEXT_PUBLIC_NETWORK=testnetAsimov
NEXT_PUBLIC_GENLAYER_RPC=
```

## Demo Flow

1. Connect wallet.
2. Open an escrow case from the handoff board.
3. Attach checkout evidence chips.
4. Run AI deposit review.
5. Release the fair refund/deduction result.
