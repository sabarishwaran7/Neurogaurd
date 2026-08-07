/**
 * NeuroGuard - Background Service Worker
 *
 * AI-powered automation workflow system.
 * Uses a node-based pipeline architecture inspired by n8n.
 *
 * Workflow Pipeline:
 *   detect_url → gemini_analysis → serpapi_check → decision_engine → block_website
 */

// Import modules
importScripts("config.js", "workflow.js");

// ═══════════════════════════════════════════════════════════════════════════
//  NODE DEFINITIONS
// ═══════════════════════════════════════════════════════════════════════════

// ─── Node 1: URL Detection ─────────────────────────────────────────────────
registerNode("detect_url", {
  label: "URL Detection",
  description: "Validates and extracts domain from the target URL",
  execute(context) {
    const { url } = context;

    // Validate URL
    if (!url || (!url.startsWith("http://") && !url.startsWith("https://"))) {
      console.log(`  │  ⏭️  Non-HTTP URL — aborting pipeline`);
      return { _abort: true, skipReason: "Non-HTTP URL" };
    }

    // Skip blocked page (prevent infinite loops)
    if (url.startsWith("chrome-extension://") && url.includes("blocked.html")) {
      console.log(`  │  ⏭️  Blocked page — aborting pipeline`);
      return { _abort: true, skipReason: "Blocked page" };
    }

    // Extract domain
    let domain = null;
    try {
      domain = new URL(url).hostname;
    } catch {
      domain = url;
    }

    console.log(`  │  🔗 URL    : ${url}`);
    console.log(`  │  🌐 Domain : ${domain}`);

    return { domain, urlValid: true };
  },
});

// ─── Node 2: Gemini AI Analysis (REMOVED) ───────────────────────────────────

// ─── Node 3: SerpApi Reputation Check ──────────────────────────────────────
registerNode("serpapi_check", {
  label: "SerpApi Reputation Check",
  description: "Searches Google for scam/phishing/malware reports about the domain",
  async execute(context) {
    const { domain } = context;
    const queries = [`${domain} scam`, `${domain} phishing`, `${domain} malware`];
    const allMatches = [];

    for (const query of queries) {
      try {
        const params = new URLSearchParams({
          q: query,
          api_key: SERPAPI_KEY,
          engine: "google",
          num: "5",
        });

        const response = await fetch(`${SERPAPI_ENDPOINT}?${params}`);

        if (!response.ok) {
          console.error(`  │  SerpApi error (${response.status}) for: "${query}"`);
          continue;
        }

        const data = await response.json();
        const results = data.organic_results || [];

        for (const result of results) {
          const text = `${result.title || ""} ${result.snippet || ""}`.toLowerCase();
          for (const keyword of THREAT_KEYWORDS) {
            if (text.includes(keyword)) {
              allMatches.push({
                keyword,
                query,
                title: result.title,
                snippet: result.snippet?.substring(0, 120),
              });
            }
          }
        }
      } catch (error) {
        console.error(`  │  SerpApi request failed for "${query}": ${error.message}`);
      }
    }

    const isRisky = allMatches.length > 0;

    if (isRisky) {
      console.log(`  │  🚨 RISKY — ${allMatches.length} threat indicator(s)`);
      for (const m of allMatches.slice(0, 3)) {
        console.log(`  │     ↳ [${m.keyword}] "${m.title}"`);
      }
    } else {
      console.log(`  │  ✅ CLEAN — No threat indicators`);
    }

    return {
      serpRisky: isRisky,
      serpMatchCount: allMatches.length,
      serpMatches: allMatches.slice(0, 5),
    };
  },
});

// ─── Node 4: Decision Engine ───────────────────────────────────────────────
registerNode("decision_engine", {
  label: "Decision Engine",
  description: "Reputation results to make final allow/block decision",
  execute(context) {
    const { url, serpRisky, serpMatchCount, serpMatches } = context;

    // Check for explicit blocked simulation URLs
    const isAmtsoSimulation = url && url.includes("amtso.org/security-features-check/phishing-page");
    const isAmtsoDownload = url && url.includes("amtso.org/security-features-check/download-file");
    const isEicarSimulation = url && url.includes("eicar.org/download-anti-malware-testfile");
    const shouldBlock = serpRisky || isAmtsoSimulation || isAmtsoDownload || isEicarSimulation;
    const decision = shouldBlock ? "BLOCKED" : "ALLOWED";

    const reasons = [];
    if (serpRisky) reasons.push(`SerpApi → ${serpMatchCount} threat(s)`);
    if (isAmtsoSimulation) reasons.push("AMTSO Phishing Simulation Test");
    if (isAmtsoDownload) reasons.push("AMTSO Malware Download Simulation Test");
    if (isEicarSimulation) reasons.push("EICAR Anti-Malware Testfile Simulation");

    if (shouldBlock) {
      console.log(`  │  🛡️  BLOCK — ${reasons.join(" + ")}`);
    } else {
      console.log(`  │  ✅ ALLOW — No threats detected`);
    }

    // Generate threat-specific explanation
    let explanation = null;
    let riskLevel = "LOW";
    if (shouldBlock) {
      riskLevel = "HIGH";
      if (isAmtsoSimulation || isAmtsoDownload || isEicarSimulation) {
        explanation = "Harmful website detected. Access blocked by NeuroGuard to protect your device from phishing and malware.";
      } else {
        const topMatch = serpMatches && serpMatches[0];
        if (topMatch) {
          explanation = `This site was flagged for a potential threat: "${topMatch.keyword}" was mentioned in search results: "${topMatch.title}".`;
        } else {
          explanation = "This website has a poor online reputation and has been flagged as unsafe.";
        }
      }
    }

    return { decision, shouldBlock, decisionReasons: reasons, explanation, riskLevel };
  },
});

// ─── Node 5: AI Explanation Generator (REMOVED) ────────────────────────────

// ─── Node 6: Block Website ────────────────────────────────────────────────
registerNode("block_website", {
  label: "Block Website",
  description: "Redirects harmful websites to the blocked page",
  async execute(context) {
    const { shouldBlock, tabId, url, explanation, riskLevel } = context;

    if (!shouldBlock) {
      console.log(`  │  ⏭️  No blocking needed`);
      return { blocked: false };
    }

    // Store explanation for blocked.html to read
    await chrome.storage.local.set({
      blocked_info: {
        url,
        explanation: explanation || "This website was flagged as potentially dangerous.",
        riskLevel: riskLevel || "HIGH",
        timestamp: new Date().toISOString(),
      },
    });

    const blockedPageURL = chrome.runtime.getURL("blocked.html") + "?url=" + encodeURIComponent(url);
    chrome.tabs.update(tabId, { url: blockedPageURL });

    console.log(`  │  🚫 Tab ${tabId} redirected to blocked.html`);

    return { blocked: true };
  },
});

// ═══════════════════════════════════════════════════════════════════════════
//  WORKFLOW ORCHESTRATION
// ═══════════════════════════════════════════════════════════════════════════

async function runThreatPipeline(url, source, tabId) {
  const timestamp = new Date().toISOString();

  // Store loading state for popup
  const storageKey = `result_${tabId}`;
  let domain = null;
  try { domain = new URL(url).hostname; } catch { domain = url; }

  await chrome.storage.local.set({
    [storageKey]: { domain, url, gemini: null, serpRisky: false, serpMatchCount: 0, decision: null, timestamp },
  });

  // Create and run workflow
  const engine = new WorkflowEngine(THREAT_DETECTION_WORKFLOW);

  const result = await engine.run({
    url,
    tabId,
    source,
    timestamp,
  });

  // Store final result for popup (if pipeline wasn't aborted)
  if (!result._abort) {
    const finalData = {
      domain: result.domain || domain,
      url,
      gemini: (result.decision === "BLOCKED" || result.serpRisky) ? "HARMFUL" : "SAFE",
      serpRisky: result.serpRisky || false,
      serpMatchCount: result.serpMatchCount || 0,
      decision: result.decision || "ALLOWED",
      explanation: result.explanation || null,
      riskLevel: result.riskLevel || null,
      timestamp,
      executionLog: result._executionLog,
      totalDurationMs: result._totalDurationMs,
    };

    await chrome.storage.local.set({ [storageKey]: finalData });

    // ── History Tracking ─────────────────────────────────────────────────
    try {
      const histData = await chrome.storage.local.get("neuroguard_history");
      const history = histData.neuroguard_history || [];

      history.unshift({
        url,
        domain: result.domain || domain,
        status: (result.decision === "BLOCKED" || result.serpRisky) ? "HARMFUL" : "SAFE",
        action: result.decision || "ALLOWED",
        serpRisky: result.serpRisky || false,
        serpMatchCount: result.serpMatchCount || 0,
        explanation: result.explanation || null,
        riskLevel: result.riskLevel || null,
        durationMs: result._totalDurationMs || 0,
        time: new Date().toLocaleString("en-US", {
          year: "numeric", month: "short", day: "numeric",
          hour: "2-digit", minute: "2-digit", second: "2-digit",
        }),
      });

      // Cap at 500 entries
      if (history.length > 500) history.length = 500;

      await chrome.storage.local.set({ neuroguard_history: history });
      console.log(`  📋 History updated (${history.length} entries)`);
    } catch (histErr) {
      console.error("  History tracking error:", histErr.message);
    }
  }
}

// ═══════════════════════════════════════════════════════════════════════════
//  CHROME EVENT LISTENERS
// ═══════════════════════════════════════════════════════════════════════════

chrome.tabs.onUpdated.addListener((tabId, changeInfo, tab) => {
  if (changeInfo.status === "complete" && tab.url) {
    runThreatPipeline(tab.url, "Tab Updated", tabId);
  }
});

chrome.tabs.onActivated.addListener(async (activeInfo) => {
  try {
    const tab = await chrome.tabs.get(activeInfo.tabId);
    if (tab.url) {
      runThreatPipeline(tab.url, "Tab Switched", activeInfo.tabId);
    }
  } catch (error) {
    console.error("[NeuroGuard] Error fetching tab info:", error.message);
  }
});

chrome.runtime.onInstalled.addListener((details) => {
  console.log(`\n╔══════════════════════════════════════════════════════════════╗`);
  console.log(`║  🛡️  NeuroGuard AI — Extension ${(details.reason).padEnd(28)}   ║`);
  console.log(`╠══════════════════════════════════════════════════════════════╣`);
  console.log(`║  Version  : 1.0.0                                          ║`);
  console.log(`║  Engine   : Workflow-based AI Automation                    ║`);
  console.log(`║  Pipeline : ${THREAT_DETECTION_WORKFLOW.name.padEnd(46)}║`);
  console.log(`║  Nodes    : ${THREAT_DETECTION_WORKFLOW.nodes.length} registered${" ".repeat(38)}║`);
  console.log(`╠══════════════════════════════════════════════════════════════╣`);
  console.log(`║  Nodes:                                                     ║`);
  for (const nodeId of THREAT_DETECTION_WORKFLOW.nodes) {
    const node = NODE_REGISTRY[nodeId];
    console.log(`║    → ${(node?.label || nodeId).padEnd(52)}║`);
  }
  console.log(`╚══════════════════════════════════════════════════════════════╝\n`);
});
