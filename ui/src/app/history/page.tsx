"use client";

import { useEffect, useState } from "react";

type HistoryRow = {
  id: number;
  image_reference: string;
  run_type: string;
  run_id: string;
  batch_id: string | null;
  predicted_gender: string | null;
  predicted_sleeve: string | null;
  gender_confidence: number | null;
  sleeve_confidence: number | null;
  model_name: string;
  model_version: string;
  status: string;
  error_message: string | null;
  created_at: string;
};

const T = {
  bg: "#F7F5F0",
  surface: "#FFFFFF",
  surfaceAlt: "#F2EFE8",
  border: "rgba(40,35,25,0.10)",
  borderStrong: "rgba(40,35,25,0.18)",
  text: "#1A1713",
  textMuted: "#7A746A",
  textFaint: "#B0A99E",
  accent: "#C8873A",
  success: "#2A7A3A",
  successBg: "#EAF5ED",
  danger: "#B83232",
  dangerBg: "#FAEAEA",
  radius: "10px",
  radiusPill: "999px",
};

function pct(value: number | null) {
  if (value === null || value === undefined) return "—";
  return `${(value * 100).toFixed(1)}%`;
}

async function fetchJson<T>(path: string): Promise<T> {
  const res = await fetch(path);
  if (!res.ok) throw new Error(`${res.status} ${res.statusText}`);
  return res.json();
}

const COLS = [
  { key: "id", label: "ID", width: 48 },
  { key: "run_type", label: "Run", width: 70 },
  { key: "image_reference", label: "Image", width: 260 },
  { key: "predicted_gender", label: "Gender", width: 80 },
  { key: "predicted_sleeve", label: "Sleeve", width: 80 },
  { key: "gender_confidence", label: "G conf", width: 72 },
  { key: "sleeve_confidence", label: "S conf", width: 72 },
  { key: "status", label: "Status", width: 80 },
  { key: "created_at", label: "Time", width: 160 },
] as const;

export default function HistoryPage() {
  const [rows, setRows] = useState<HistoryRow[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");

  async function load() {
    setLoading(true);
    setError(null);
    try {
      const data = await fetchJson<HistoryRow[]>("/api/history?limit=200");
      setRows(data);
    } catch (e) {
      setError(String(e));
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => { load(); }, []);

  const filtered = search.trim()
    ? rows.filter(
        (r) =>
          r.image_reference.toLowerCase().includes(search.toLowerCase()) ||
          r.run_type.toLowerCase().includes(search.toLowerCase()) ||
          (r.predicted_gender ?? "").toLowerCase().includes(search.toLowerCase()) ||
          (r.predicted_sleeve ?? "").toLowerCase().includes(search.toLowerCase())
      )
    : rows;

  const baseBtn: React.CSSProperties = {
    fontSize: 12, padding: "6px 14px",
    borderRadius: T.radiusPill,
    cursor: "pointer", fontFamily: "inherit",
    border: `1px solid ${T.border}`,
    background: "transparent", color: T.text,
    textDecoration: "none",
    display: "inline-flex", alignItems: "center",
  };

  return (
    <div style={{
      display: "flex", flexDirection: "column",
      height: "100vh", overflow: "hidden",
      background: T.bg, fontFamily: "inherit",
    }}>
      {/* Topbar */}
      <header style={{
        display: "flex", alignItems: "center",
        justifyContent: "space-between",
        padding: "0 24px", height: 56,
        background: T.surface,
        borderBottom: `1px solid ${T.border}`,
        flexShrink: 0, gap: 16,
      }}>
        <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
          <div style={{
            width: 30, height: 30, borderRadius: 8,
            background: T.accent,
            display: "flex", alignItems: "center", justifyContent: "center",
          }}>
            <svg width="15" height="15" viewBox="0 0 14 14" fill="none">
              <rect x="1" y="3" width="5" height="8" rx="1.2" fill="white" fillOpacity="0.9"/>
              <rect x="8" y="1" width="5" height="5" rx="1.2" fill="white"/>
              <rect x="8" y="8" width="5" height="4" rx="1.2" fill="white" fillOpacity="0.6"/>
            </svg>
          </div>
          <div>
            <div style={{ fontSize: 15, fontWeight: 600, color: T.text, letterSpacing: "-0.2px" }}>
              History
            </div>
            <div style={{ fontSize: 10, color: T.textMuted, marginTop: 1 }}>
              Prediction tracking · SQLite
            </div>
          </div>
        </div>

        <nav style={{ display: "flex", gap: 8, alignItems: "center" }}>
          {/* Search */}
          <input
            type="text"
            placeholder="Search…"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            style={{
              fontSize: 12, padding: "6px 14px",
              borderRadius: T.radiusPill,
              border: `1px solid ${T.border}`,
              background: T.surfaceAlt, color: T.text,
              outline: "none", fontFamily: "inherit",
              width: 180,
            }}
          />
          <a href="/" style={baseBtn}>Products</a>
          <button style={baseBtn} onClick={load} disabled={loading}>
            Refresh
          </button>
          {rows.length > 0 && (
            <span style={{
              fontSize: 11, color: T.textMuted,
              background: T.surfaceAlt,
              borderRadius: T.radiusPill, padding: "4px 12px",
              border: `1px solid ${T.border}`,
            }}>
              {filtered.length}{search ? ` / ${rows.length}` : ""} records
            </span>
          )}
        </nav>
      </header>

      {/* Table area */}
      <div style={{ flex: 1, minHeight: 0, overflowY: "auto", padding: "16px 24px" }}>
        {error && (
          <div style={{
            fontSize: 13, color: T.danger,
            background: T.dangerBg,
            borderRadius: T.radius, padding: "10px 14px",
            marginBottom: 14,
            border: `1px solid rgba(184,50,50,0.18)`,
          }}>
            Failed to load: {error}
          </div>
        )}

        <div style={{
          background: T.surface,
          borderRadius: T.radius,
          border: `1px solid ${T.border}`,
          overflow: "hidden",
        }}>
          <table style={{
            width: "100%", borderCollapse: "collapse",
            fontSize: 12, tableLayout: "fixed",
          }}>
            <colgroup>
              {COLS.map((c) => (
                <col key={c.key} style={{ width: c.width }} />
              ))}
            </colgroup>

            <thead>
              <tr style={{ background: T.surfaceAlt }}>
                {COLS.map((c) => (
                  <th key={c.key} style={{
                    padding: "10px 12px",
                    borderBottom: `1px solid ${T.border}`,
                    textAlign: "left",
                    fontSize: 10, fontWeight: 600,
                    color: T.textFaint,
                    textTransform: "uppercase",
                    letterSpacing: "0.07em",
                    whiteSpace: "nowrap",
                    overflow: "hidden",
                    textOverflow: "ellipsis",
                  }}>
                    {c.label}
                  </th>
                ))}
              </tr>
            </thead>

            <tbody>
              {loading && (
                <tr>
                  <td colSpan={COLS.length} style={{ padding: "20px 14px", color: T.textMuted, fontSize: 13 }}>
                    Loading…
                  </td>
                </tr>
              )}
              {!loading && filtered.length === 0 && (
                <tr>
                  <td colSpan={COLS.length} style={{ padding: "20px 14px", color: T.textFaint, fontSize: 13 }}>
                    {search ? "No records match your search." : "No prediction records yet."}
                  </td>
                </tr>
              )}
              {filtered.map((r, i) => (
                <tr
                  key={r.id}
                  style={{
                    background: i % 2 === 0 ? T.surface : T.surfaceAlt,
                    transition: "background 0.1s",
                  }}
                >
                  {/* ID */}
                  <td style={cellStyle}>{r.id}</td>

                  {/* Run type */}
                  <td style={cellStyle}>
                    <span style={{
                      fontSize: 10, padding: "2px 8px",
                      borderRadius: T.radiusPill,
                      background: r.run_type === "batch" ? "#E6F1FB" : T.surfaceAlt,
                      color: r.run_type === "batch" ? "#185FA5" : T.textMuted,
                      fontWeight: 500,
                    }}>
                      {r.run_type}
                    </span>
                  </td>

                  {/* Image reference */}
                  <td style={{ ...cellStyle, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}
                    title={r.image_reference}>
                    <span style={{ color: T.textMuted }}>{r.image_reference}</span>
                  </td>

                  {/* Gender */}
                  <td style={cellStyle}>{r.predicted_gender || <span style={{ color: T.textFaint }}>—</span>}</td>

                  {/* Sleeve */}
                  <td style={cellStyle}>{r.predicted_sleeve || <span style={{ color: T.textFaint }}>—</span>}</td>

                  {/* Confidences */}
                  <td style={{ ...cellStyle, color: T.textMuted }}>{pct(r.gender_confidence)}</td>
                  <td style={{ ...cellStyle, color: T.textMuted }}>{pct(r.sleeve_confidence)}</td>

                  {/* Status */}
                  <td style={cellStyle}>
                    <span style={{
                      fontSize: 10, fontWeight: 500,
                      padding: "2px 8px", borderRadius: T.radiusPill,
                      background: r.status === "success" ? T.successBg : T.dangerBg,
                      color: r.status === "success" ? T.success : T.danger,
                    }}>
                      {r.status}
                    </span>
                  </td>

                  {/* Time */}
                  <td style={{ ...cellStyle, color: T.textMuted, whiteSpace: "nowrap" }}>
                    {r.created_at}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}

const cellStyle: React.CSSProperties = {
  padding: "9px 12px",
  borderBottom: "1px solid rgba(40,35,25,0.06)",
  color: "#1A1713",
  fontSize: 12,
  verticalAlign: "middle",
};
