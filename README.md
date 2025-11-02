# Telegram Bot — Hyperliquid / LPVault Trading Assistant

This repository contains a **Telegram bot** designed to manage **Hyperliquid trading** and **LPVault operations** through conversational workflows.
It enables users to trade, manage wallets, monitor balances, perform DCA or grid strategies, and interact with on-chain assets — all directly from Telegram.

> ⚠️ **Disclaimer:** This bot is provided for educational and experimental purposes only. Use at your own risk. Cryptocurrency trading carries a risk of financial loss.

> ⚙️ **Note:**  
> This repository represents **only a part of the entire service**.  
> It cannot be run independently — some components and dependencies are external or private.

---

## 🚀 Features

### 🔐 Wallet Management

* Create / Import / Export / Delete wallets
* Authenticate or switch wallets
* Manage EVM accounts seamlessly

### 💰 Balances

* View **spot** and **perpetual** balances
* Check detailed asset positions
* Transfer between spot ↔ perp accounts
* Perform on-chain balance refresh

### 📈 Trading Modules

* **Spot Trading:** Buy/Sell specific or all assets
* **Perp Trading:** Open/close single or all perpetual positions
* **DCA (Dollar-Cost Averaging):** Create and manage automated buying plans
* **Delta Strategies:** Open/close delta-neutral positions
* **Grid Trading:** Spot and perp grid trading strategies
* **Copy Trading:**

  * Follow / Unfollow traders
  * Adjust leverage & order value
  * Configure PnL alerts and auto-refresh
* **Rebalancing:**

  * Register, update, or remove rebalancing strategies
  * Configure profit/loss alerts

### 🌉 LPVault & Bridge

* Register / Unregister vaults
* Manual minting and swapping
* Bridge wrap / unwrap utilities
* Vault refresh and state management

### 🧾 Referrals

* View referral details
* Manage referral registration

### ⚙️ Utility & Admin

* Pagination helpers
* State machine for conversational flow
* Centralized exception handling

---

## 🧠 Tech Stack

* **Python 3.11+**
* **uv** package manager (`uv.lock`)
* **State machine-based architecture** for Telegram interaction
* **API abstraction layer** under `src/api` (Hyperliquid, LPVault, bridge)
* **Containerized** via Docker

---

## 📁 Project Structure (Simplified)

```
src/
├── app.py                 # Entry point for the Telegram bot
├── api/                   # External API & blockchain interaction
│   ├── hyperliquid/       # HL spot/perp/copy/delta/grid modules
│   ├── lpvault.py         # LPVault integration
│   ├── bridge.py          # Bridge utilities
│   └── models/            # Shared data models
├── handler/               # Telegram handlers (command flows)
│   ├── wallet/            # Wallet operations
│   ├── hyperliquid/       # HL trading flows (buy/sell/grid/delta/etc.)
│   ├── evm/lpvault/       # LPVault workflows
│   ├── referral/          # Referral handling
│   └── start/             # /start and onboarding
└── api/models/            # API data structures
```

---

## 🧩 Installation & Setup

### 0️⃣ Requirements

* Python 3.11 or later
* [uv](https://github.com/astral-sh/uv) (recommended for dependency management)

### 1️⃣ Install Dependencies

```bash
uv sync
```

### 2️⃣ Environment Variables

Create a `.env` file in the project root:

```dotenv
# Telegram
TELEGRAM_BOT_TOKEN=123456:abcdefg

# Optional webhook settings
WEBHOOK_URL=https://your.domain.com/telegram/webhook
WEBHOOK_SECRET=supersecret
```

## 🧱 Development Notes

* Modular handler design allows easy feature expansion.
* Each flow (`buy`, `sell`, `dca`, etc.) uses **`states.py` + `settings.py`** for conversation state tracking.
* Common helpers for account, pagination, and exceptions live in `handler/utils/`.
* API clients (`src/api`) are reusable across handlers.

---

📜 License — Non-Commercial Use Only

This project is licensed under the Non-Commercial License (NC).
You may use, modify, and distribute this software for personal or academic purposes only.
Commercial use, resale, or integration into profit-generating services is strictly prohibited.