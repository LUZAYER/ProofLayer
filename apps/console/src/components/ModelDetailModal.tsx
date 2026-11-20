"use client";

import React from "react";

export interface ModelSpec {
  id: string;
  name: string;
  codename: string;
  type: string;
  architecture: string;
  parameters?: string;
  latency: string;
  precision: string;
  languages: string[];
  description: string;
  trainingDetails: string;
  benchmarks: {
    metric: string;
    value: string;
    baseline: string;
  }[];
  sampleInput: string;
  sampleOutput: string;
  tags: string[];
}

interface ModelDetailModalProps {
  model: ModelSpec | null;
  onClose: () => void;
  lang?: "en" | "bn";
}

export default function ModelDetailModal({ model, onClose, lang = "en" }: ModelDetailModalProps) {
  if (!model) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/70 backdrop-blur-md animate-fadeIn">
      <div
        className="w-full max-w-3xl max-h-[90vh] overflow-y-auto rounded-2xl bg-surface border border-outline-variant/30 shadow-2xl flex flex-col"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="px-6 py-5 border-b border-outline-variant/20 flex items-start justify-between bg-surface-container-low sticky top-0 z-10">
          <div>
            <div className="flex items-center gap-2 mb-1">
              <span className="px-2.5 py-0.5 rounded-full text-xs font-semibold bg-primary/10 text-primary border border-primary/20">
                {model.type}
              </span>
              <span className="text-xs font-mono text-outline">{model.codename}</span>
            </div>
            <h2 className="text-xl font-bold text-on-surface">{model.name}</h2>
          </div>
          <button
            onClick={onClose}
            className="p-1.5 rounded-lg text-outline hover:text-on-surface hover:bg-surface-container-high transition-colors"
            aria-label="Close modal"
          >
            <span className="material-symbols-outlined text-[20px]">close</span>
          </button>
        </div>

        {/* Body */}
        <div className="p-6 space-y-6">
          {/* Key Stats Bar */}
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 p-4 rounded-xl bg-surface-container-low border border-outline-variant/20">
            <div>
              <span className="text-xs text-outline block uppercase tracking-wider font-mono">
                p95 Latency
              </span>
              <span className="text-lg font-bold text-primary font-mono">{model.latency}</span>
            </div>
            <div>
              <span className="text-xs text-outline block uppercase tracking-wider font-mono">
                Accuracy / F1
              </span>
              <span className="text-lg font-bold text-tertiary font-mono">{model.precision}</span>
            </div>
            <div>
              <span className="text-xs text-outline block uppercase tracking-wider font-mono">
                Architecture
              </span>
              <span className="text-xs font-semibold text-on-surface block mt-1">
                {model.architecture}
              </span>
            </div>
            <div>
              <span className="text-xs text-outline block uppercase tracking-wider font-mono">
                Languages
              </span>
              <div className="flex gap-1 mt-1">
                {model.languages.map((l) => (
                  <span
                    key={l}
                    className="px-1.5 py-0.5 rounded text-[10px] font-mono font-semibold bg-surface-container text-on-surface border border-outline-variant/30"
                  >
                    {l}
                  </span>
                ))}
              </div>
            </div>
          </div>

          {/* Description */}
          <div>
            <h3 className="text-sm font-semibold text-outline uppercase tracking-wider mb-2 font-mono">
              Model Purpose & Overview
            </h3>
            <p className="text-sm text-on-surface leading-relaxed">{model.description}</p>
          </div>

          {/* Training & Pipeline Details */}
          <div>
            <h3 className="text-sm font-semibold text-outline uppercase tracking-wider mb-2 font-mono">
              Training Pipeline & Mathematical Grounding
            </h3>
            <div className="p-4 rounded-xl bg-surface-container border border-outline-variant/20 text-xs text-on-surface-variant leading-relaxed">
              {model.trainingDetails}
            </div>
          </div>

          {/* Benchmark Results */}
          <div>
            <h3 className="text-sm font-semibold text-outline uppercase tracking-wider mb-2 font-mono">
              Empirical Benchmark Outcomes
            </h3>
            <div className="border border-outline-variant/20 rounded-xl overflow-hidden">
              <table className="w-full text-left text-xs">
                <thead className="bg-surface-container-high border-b border-outline-variant/20 text-outline uppercase tracking-wider">
                  <tr>
                    <th className="py-2.5 px-4 font-semibold">Evaluation Metric</th>
                    <th className="py-2.5 px-4 font-semibold">ProofLayer Score</th>
                    <th className="py-2.5 px-4 font-semibold">Standard Baseline</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-outline-variant/10 font-mono">
                  {model.benchmarks.map((b, idx) => (
                    <tr key={idx} className="hover:bg-surface-container/50">
                      <td className="py-2.5 px-4 text-on-surface">{b.metric}</td>
                      <td className="py-2.5 px-4 text-primary font-bold">{b.value}</td>
                      <td className="py-2.5 px-4 text-outline">{b.baseline}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          {/* Live Sample I/O */}
          <div>
            <h3 className="text-sm font-semibold text-outline uppercase tracking-wider mb-2 font-mono">
              Sample Inference Preview
            </h3>
            <div className="space-y-2">
              <div className="p-3 rounded-lg bg-surface-container border border-outline-variant/20">
                <span className="text-[11px] font-mono text-outline block mb-1">
                  INPUT PAYLOAD:
                </span>
                <code className="text-xs text-on-surface font-mono break-all block">
                  {model.sampleInput}
                </code>
              </div>
              <div className="p-3 rounded-lg bg-surface-container-low border border-primary/30">
                <span className="text-[11px] font-mono text-primary block mb-1">
                  INTERCEPTION RESULT:
                </span>
                <code className="text-xs text-primary font-mono break-all block">
                  {model.sampleOutput}
                </code>
              </div>
            </div>
          </div>
        </div>

        {/* Footer */}
        <div className="px-6 py-4 border-t border-outline-variant/20 bg-surface-container-low flex justify-end">
          <button
            onClick={onClose}
            className="px-5 py-2 rounded-xl bg-primary text-on-primary font-semibold text-xs shadow-md hover:bg-primary-container hover:text-on-primary-container transition-all"
          >
            Close Spec Sheet
          </button>
        </div>
      </div>
    </div>
  );
}
