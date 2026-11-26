# CogKura Demo 0.3.18 — Core 0.20.3

The API depends on `cogkura>=0.20.3,<0.20.4`; the lock selects the released PyPI 0.20.3 wheel. Live Memory and Compare continue to use Core's `prepare_context()` and existing subject-scoped processing. The demo does not enable interference or inhibition or repair Core retrieval.

On the standard waterproof-jacket prompt, inspect-only Compare produced the same results as the recorded 0.3.17 / Core 0.17.7 baseline:

| Strategy | Tokens | Units | Labelled coverage | Stale labelled concepts | Units with stale evidence |
| --- | ---: | ---: | ---: | ---: | ---: |
| Full History | 2335 | 134 | 5/5 | 2 | 8 |
| Search (BM25) | 703 | 34 | 4/5 | 2 | 5 |
| CogKura | 40 | 5 | 5/5 | 1 | 1 |

The one stale CogKura concept is old size L in supporting evidence, not in the rendered context. These labels are demo-owned and do not represent a general benchmark.

After the live statement “Actually, I'm back to a large now,” Core reports a conflict, with size L contested and the existing size M active at the session time. The immediate rendered context includes the new large statement. This differs from the prior test's contested M/L expectation and does not establish that the current-size conflict is resolved. The demo reports the Core state rather than rewriting it.

Tests disable any locally configured OpenAI key so inspect-only tests cannot accidentally make model requests. Tests using fake model responses remain separate from actual model integration.
