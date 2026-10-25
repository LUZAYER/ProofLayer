/**
 * ProofLayer TypeScript Client SDK
 */

export interface ScanSegment {
  text: string;
  provenance: "SYSTEM" | "USER" | "TOOL_OUTPUT" | "RETRIEVED_DOC" | "WEB";
  language_hint?: string;
}

export interface ScanResult {
  decision: "ALLOW" | "ALLOW_WITH_REDACTION" | "REQUIRE_APPROVAL" | "BLOCK";
  risk_score: number;
  categories: string[];
  explanation: { en: string; bn: string };
  spotlighted_content?: string;
  audit_sequence?: number;
  latency_ms: number;
}

export interface ToolAuthorizeResult {
  decision: "ALLOW" | "DENY" | "REQUIRE_APPROVAL";
  effective_decision: "ALLOW" | "DENY" | "REQUIRE_APPROVAL";
  reasons: string[];
  requires_approval: boolean;
  approval_id?: string;
}

export class ProofLayer {
  private baseUrl: string;
  private apiKey?: string;
  private agentId: string;

  constructor(options?: { baseUrl?: string; apiKey?: string; agentId?: string }) {
    this.baseUrl = (options?.baseUrl || "http://localhost:8000").replace(/\/$/, "");
    this.apiKey = options?.apiKey;
    this.agentId = options?.agentId || "default-agent";
  }

  private async fetchJson<T>(path: string, body: unknown): Promise<T> {
    const headers: Record<string, string> = {
      "Content-Type": "application/json",
      "X-ProofLayer-Agent": this.agentId,
    };
    if (this.apiKey) {
      headers["Authorization"] = `Bearer ${this.apiKey}`;
    }

    const response = await fetch(`${this.baseUrl}${path}`, {
      method: "POST",
      headers,
      body: JSON.stringify(body),
    });

    if (!response.ok) {
      throw new Error(`ProofLayer API Error: ${response.status} ${response.statusText}`);
    }

    return response.json() as Promise<T>;
  }

  async scan(segments: ScanSegment[]): Promise<ScanResult> {
    return this.fetchJson<ScanResult>("/v1/shield/scan", { segments });
  }

  async authorizeTool(toolName: string, args: Record<string, unknown>, context?: Record<string, unknown>): Promise<ToolAuthorizeResult> {
    return this.fetchJson<ToolAuthorizeResult>("/v1/tools/authorize", {
      agent_id: this.agentId,
      tool_name: toolName,
      arguments: args,
      context: context || {},
    });
  }
}
