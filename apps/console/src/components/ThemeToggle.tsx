"use client";

import React, { useState, useEffect } from "react";

interface ThemeToggleProps {
  className?: string;
}

export default function ThemeToggle({ className = "" }: ThemeToggleProps) {
  const [theme, setTheme] = useState<"dark" | "light">("dark");
  const [mounted, setMounted] = useState<boolean>(false);

  useEffect(() => {
    setMounted(true);
    // Check initial theme from localStorage or document element
    const savedTheme = localStorage.getItem("prooflayer-theme") as "dark" | "light" | null;
    if (savedTheme) {
      setTheme(savedTheme);
      if (savedTheme === "dark") {
        document.documentElement.classList.add("dark");
      } else {
        document.documentElement.classList.remove("dark");
      }
    } else {
      // Default to dark mode (Cyber Obsidian)
      document.documentElement.classList.add("dark");
      setTheme("dark");
    }
  }, []);

  const toggleTheme = () => {
    const newTheme = theme === "dark" ? "light" : "dark";
    
    // Add extraordinary transition class to HTML root
    document.documentElement.classList.add("theme-transition");
    
    if (newTheme === "dark") {
      document.documentElement.classList.add("dark");
    } else {
      document.documentElement.classList.remove("dark");
    }
    
    setTheme(newTheme);
    localStorage.setItem("prooflayer-theme", newTheme);

    // Remove transition class after animation completes
    setTimeout(() => {
      document.documentElement.classList.remove("theme-transition");
    }, 450);
  };

  if (!mounted) {
    return (
      <div className={`w-14 h-7 rounded-full bg-surface-container border border-outline-variant/30 ${className}`} />
    );
  }

  const isDark = theme === "dark";

  return (
    <button
      onClick={toggleTheme}
      type="button"
      role="switch"
      aria-checked={isDark}
      aria-label={`Toggle theme: Currently ${isDark ? "Cyber Obsidian (Dark)" : "Quantum Light (Light)"}`}
      title={`Switch to ${isDark ? "Quantum Light (Executive Ivory)" : "Cyber Obsidian (Dark)"}`}
      className={`group relative inline-flex h-8 w-16 items-center rounded-full p-0.5 transition-all duration-300 focus:outline-none focus:ring-2 focus:ring-primary/50 shadow-inner ${
        isDark
          ? "bg-surface-container-high border border-primary/30 hover:border-primary/60 shadow-[0_0_12px_rgba(87,241,219,0.15)]"
          : "bg-surface-container border border-outline-variant/40 hover:border-primary/50 shadow-[0_0_12px_rgba(13,148,136,0.15)]"
      } ${className}`}
    >
      {/* Background Track Icons */}
      <div className="absolute inset-0 flex items-center justify-between px-2 text-[13px] pointer-events-none select-none">
        <span
          className={`transition-opacity duration-300 ${
            isDark ? "text-primary/70 opacity-100" : "text-outline/40 opacity-40"
          }`}
        >
          <span className="material-symbols-outlined text-[13px]">dark_mode</span>
        </span>
        <span
          className={`transition-opacity duration-300 ${
            !isDark ? "text-amber-500 opacity-100" : "text-outline/40 opacity-40"
          }`}
        >
          <span className="material-symbols-outlined text-[13px]">light_mode</span>
        </span>
      </div>

      {/* Floating Animated Thumb */}
      <span
        className={`pointer-events-none inline-block h-6 w-6 transform rounded-full shadow-lg transition-transform duration-300 ease-out flex items-center justify-center relative z-10 ${
          isDark
            ? "translate-x-0.5 bg-gradient-to-tr from-surface-container-lowest via-primary/30 to-primary text-primary border border-primary/50"
            : "translate-x-8 bg-gradient-to-tr from-amber-400 to-amber-200 text-amber-900 border border-amber-300/80 shadow-[0_0_10px_rgba(245,158,11,0.5)]"
        }`}
      >
        {isDark ? (
          <span className="material-symbols-outlined text-[13px] animate-pulse">
            nights_stay
          </span>
        ) : (
          <span className="material-symbols-outlined text-[13px] animate-[spin_8s_linear_infinite]">
            wb_sunny
          </span>
        )}
      </span>
    </button>
  );
}
