# Onboarding

- [Gate A — API Key](gate_a_api_key.md) — Gemini API key validation and health check. Key lives in `.env`, validate-key calls Gemini models list.
- [Gate B — WhatsApp Bridge](gate_b_bridge.md) — Bridge pairing status polling. Auto-connects if already paired. Status check via port 8080 + process existence.
- [Gate C — Group Whitelisting](gate_c_whitelist.md) — Chat classification and group selection. Uses v1 classify endpoint, saves to v2 groups table with TLDRs.
