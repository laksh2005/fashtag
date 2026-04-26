"use client";

import { useEffect, useMemo, useState } from "react";

type Product = {
  image_path: string;
  image_web_path: string | null;
  product_title: string;
  brand: string;
  class_name: string;
  gender: string;
  sleeve: string;
  product_url: string;
  image_url: string;
};

type PredictionRow = {
  image_reference: string;
  predicted_gender: string | null;
  predicted_sleeve: string | null;
  gender_confidence: number | null;
  sleeve_confidence: number | null;
  model_name: string;
  model_version: string;
  status: "success" | "error";
  error_message?: string | null;
};

type FilterKey = "all" | "men-full" | "men-half" | "women-full" | "women-half";

const FILTERS: { key: FilterKey; label: string }[] = [
  { key: "all", label: "All" },
  { key: "men-full", label: "Men · Full" },
  { key: "men-half", label: "Men · Half" },
  { key: "women-full", label: "Women · Full" },
  { key: "women-half", label: "Women · Half" },
];

const T = {
  bg: "#F7F5F0",
  surface: "#FFFFFF",
  surfaceAlt: "#F2EFE8",
  border: "rgba(40,35,25,0.10)",
  borderStrong: "rgba(40,35,25,0.22)",
  text: "#1A1713",
  textMuted: "#7A746A",
  textFaint: "#B0A99E",
  accent: "#C8873A",
  accentBg: "#FDF3E7",
  accentText: "#7A4A0E",
  success: "#2A7A3A",
  successBg: "#EAF5ED",
  danger: "#B83232",
  dangerBg: "#FAEAEA",
  radius: "10px",
  radiusSm: "6px",
  radiusPill: "999px",
};

function pct(v: number | null) {
  if (v === null || v === undefined) return "—";
  return `${(v * 100).toFixed(1)}%`;
}

async function fetchJson<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(path, init);
  if (!res.ok) throw new Error(`${res.status} ${res.statusText}`);
  return res.json();
}

function filterKeyOf(p: Product) {
  const genderKey =
    p.gender === "male" ? "men" :
    p.gender === "female" ? "women" :
    p.gender;
  const sleeveKey =
    p.sleeve === "full_sleeve" ? "full" :
    p.sleeve === "half_sleeve" ? "half" :
    p.sleeve;
  return `${genderKey}-${sleeveKey}`;
}

export default function HomePage() {
  const [products, setProducts] = useState<Product[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selected, setSelected] = useState<Record<string, boolean>>({});
  const [latest, setLatest] = useState<PredictionRow | null>(null);
  const [activeFilter, setActiveFilter] = useState<FilterKey>("all");

  const selectedList = useMemo(
    () => Object.keys(selected).filter((k) => selected[k]),
    [selected]
  );

  const visibleProducts = useMemo(() => {
    if (activeFilter === "all") return products;
    return products.filter((p) => filterKeyOf(p) === activeFilter);
  }, [products, activeFilter]);

  async function loadProducts() {
    setLoading(true);
    setError(null);
    try {
      const data = await fetchJson<Product[]>("/api/products?limit=200");
      setProducts(data);
    } catch (e) {
      setError(String(e));
    } finally {
      setLoading(false);
    }
  }

  async function predictSingle(image_path: string) {
    setLatest(null);
    try {
      const result = await fetchJson<PredictionRow>("/api/predict-single", {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({ image_reference: image_path }),
      });
      setLatest(result);
    } catch (e) {
      setLatest({
        image_reference: image_path,
        predicted_gender: null,
        predicted_sleeve: null,
        gender_confidence: null,
        sleeve_confidence: null,
        model_name: "multitask_resnet18",
        model_version: "unknown",
        status: "error",
        error_message: String(e),
      });
    }
  }

  async function predictBatch() {
    if (!selectedList.length) return;
    setLatest(null);
    try {
      const result = await fetchJson<any>("/api/predict-batch", {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({ image_references: selectedList }),
      });
      setLatest({
        image_reference: `${result.total_items} items`,
        predicted_gender: null,
        predicted_sleeve: null,
        gender_confidence: null,
        sleeve_confidence: null,
        model_name: "multitask_resnet18",
        model_version: "batch",
        status: "success",
        error_message: `batch_id=${result.batch_id}  ·  success=${result.success_count}  ·  errors=${result.error_count}`,
      });
    } catch (e) {
      setLatest({
        image_reference: `${selectedList.length} items`,
        predicted_gender: null,
        predicted_sleeve: null,
        gender_confidence: null,
        sleeve_confidence: null,
        model_name: "multitask_resnet18",
        model_version: "batch",
        status: "error",
        error_message: String(e),
      });
    }
  }

  useEffect(() => { loadProducts(); }, []);

  const baseBtn: React.CSSProperties = {
    fontSize: 12, padding: "6px 14px",
    borderRadius: T.radiusPill,
    cursor: "pointer", fontFamily: "inherit",
    transition: "opacity 0.13s",
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
              FashTag
            </div>
            <div style={{ fontSize: 10, color: T.textMuted, marginTop: 1 }}>
              Products · predictions
            </div>
          </div>
        </div>

        <nav style={{ display: "flex", gap: 8, alignItems: "center" }}>
          <a href="/history" style={{ ...baseBtn, border: `1px solid ${T.border}`, background: "transparent", color: T.text }}>
            History
          </a>
          <button
            style={{ ...baseBtn, border: `1px solid ${T.border}`, background: "transparent", color: T.text }}
            onClick={loadProducts}
            disabled={loading}
          >
            Refresh
          </button>
          <button
            onClick={predictBatch}
            disabled={selectedList.length === 0}
            style={{
              ...baseBtn,
              border: "none",
              background: T.accent,
              color: "#fff",
              fontWeight: 500,
              opacity: selectedList.length === 0 ? 0.4 : 1,
              cursor: selectedList.length === 0 ? "not-allowed" : "pointer",
            }}
          >
            Predict batch
            {selectedList.length > 0 && (
              <span style={{
                marginLeft: 7, fontSize: 11,
                background: "rgba(255,255,255,0.25)",
                borderRadius: 999, padding: "1px 7px",
              }}>
                {selectedList.length}
              </span>
            )}
          </button>
        </nav>
      </header>

      {/* Body */}
      <div style={{
        display: "grid",
        gridTemplateColumns: "1fr 272px",
        flex: 1, minHeight: 0,
      }}>
        {/* Left */}
        <div style={{
          display: "flex", flexDirection: "column",
          minHeight: 0,
          borderRight: `1px solid ${T.border}`,
        }}>
          {/* Filter bar */}
          <div style={{
            display: "flex", alignItems: "center",
            gap: 6, padding: "9px 16px",
            background: T.surface,
            borderBottom: `1px solid ${T.border}`,
            flexShrink: 0, flexWrap: "wrap",
          }}>
            <span style={{
              fontSize: 10, color: T.textFaint,
              fontWeight: 600, textTransform: "uppercase",
              letterSpacing: "0.07em", marginRight: 4,
            }}>
              Filter
            </span>
            {FILTERS.map((f) => {
              const active = activeFilter === f.key;
              return (
                <button
                  key={f.key}
                  onClick={() => setActiveFilter(f.key)}
                  style={{
                    fontSize: 12, padding: "4px 13px",
                    borderRadius: T.radiusPill,
                    border: active ? "none" : `1px solid ${T.border}`,
                    background: active ? T.accent : "transparent",
                    color: active ? "#fff" : T.textMuted,
                    fontWeight: active ? 500 : 400,
                    cursor: "pointer", transition: "all 0.14s",
                    fontFamily: "inherit", whiteSpace: "nowrap",
                  }}
                >
                  {f.label}
                </button>
              );
            })}
            <span style={{
              marginLeft: "auto", fontSize: 11,
              color: T.textMuted,
              background: T.surfaceAlt,
              borderRadius: T.radiusPill, padding: "3px 11px",
              border: `1px solid ${T.border}`,
            }}>
              {visibleProducts.length}
            </span>
          </div>

          {/* 5-col scrollable grid */}
          <div style={{ flex: 1, overflowY: "auto", padding: "14px 16px" }}>
            {error && (
              <p style={{ color: T.danger, fontSize: 13, marginBottom: 12 }}>
                Failed to load: {error}
              </p>
            )}
            {loading ? (
              <p style={{ fontSize: 13, color: T.textMuted }}>Loading…</p>
            ) : (
              <div style={{
                display: "grid",
                gridTemplateColumns: "repeat(5, 1fr)",
                gap: 10,
              }}>
                {visibleProducts.map((p) => (
                  <ProductCard
                    key={p.image_path}
                    product={p}
                    checked={!!selected[p.image_path]}
                    onCheck={(v) => setSelected((s) => ({ ...s, [p.image_path]: v }))}
                    onPredict={() => predictSingle(p.image_path)}
                  />
                ))}
              </div>
            )}
          </div>
        </div>

        {/* Right */}
        <aside style={{
          display: "flex", flexDirection: "column",
          padding: 18, gap: 14,
          background: T.surface,
          overflowY: "auto",
        }}>
          <div>
            <div style={{ fontSize: 14, fontWeight: 600, color: T.text }}>Latest result</div>
            <div style={{ fontSize: 11, color: T.textMuted, marginTop: 3 }}>Logged to SQLite via API</div>
          </div>

          <div style={{ height: 1, background: T.border }} />

          <div style={{
            flex: 1, borderRadius: T.radius,
            border: `1px solid ${T.border}`,
            background: T.surfaceAlt,
            padding: 14,
          }}>
            {!latest ? (
              <p style={{ fontSize: 12, color: T.textFaint, lineHeight: 1.6 }}>
                Click Predict on any product card to see model output here.
              </p>
            ) : (
              <div>
                <div style={{
                  display: "flex", alignItems: "center",
                  justifyContent: "space-between", marginBottom: 12,
                }}>
                  <span style={{
                    fontSize: 11, color: T.textMuted,
                    overflow: "hidden", textOverflow: "ellipsis",
                    whiteSpace: "nowrap", maxWidth: 160,
                  }}>
                    {latest.image_reference.split("/").pop()}
                  </span>
                  <StatusBadge status={latest.status} />
                </div>

                <ResultRow label="Gender" value={latest.predicted_gender} conf={latest.gender_confidence} />
                <ResultRow label="Sleeve" value={latest.predicted_sleeve} conf={latest.sleeve_confidence} />

                {latest.error_message && (
                  <div style={{
                    marginTop: 10, fontSize: 11,
                    color: T.textMuted, wordBreak: "break-all", lineHeight: 1.5,
                  }}>
                    {latest.error_message}
                  </div>
                )}

                <div style={{
                  marginTop: 14, paddingTop: 12,
                  borderTop: `1px solid ${T.border}`,
                }}>
                  <div style={{
                    fontSize: 10, color: T.textFaint, fontWeight: 600,
                    textTransform: "uppercase", letterSpacing: "0.06em", marginBottom: 4,
                  }}>
                    Model
                  </div>
                  <div style={{ fontSize: 12, color: T.text }}>{latest.model_name}</div>
                  <div style={{ fontSize: 11, color: T.textMuted, marginTop: 2 }}>v{latest.model_version}</div>
                </div>
              </div>
            )}
          </div>

          {selectedList.length > 0 && (
            <div style={{
              borderRadius: T.radius,
              border: `1px solid rgba(200,135,58,0.30)`,
              background: T.accentBg,
              padding: "10px 14px",
            }}>
              <div style={{ fontSize: 11, color: T.accentText, fontWeight: 500 }}>
                {selectedList.length} selected for batch
              </div>
              <button
                onClick={() => setSelected({})}
                style={{
                  marginTop: 5, fontSize: 11, color: T.textMuted,
                  background: "none", border: "none",
                  cursor: "pointer", padding: 0, fontFamily: "inherit",
                  textDecoration: "underline",
                }}
              >
                Clear selection
              </button>
            </div>
          )}
        </aside>
      </div>
    </div>
  );
}

function ProductCard({
  product: p,
  checked,
  onCheck,
  onPredict,
}: {
  product: Product;
  checked: boolean;
  onCheck: (v: boolean) => void;
  onPredict: () => void;
}) {
  const imgSrc = p.image_web_path ?? "";
  const isMen = p.gender === "men" || p.gender === "male";
  const chipStyle: React.CSSProperties = {
    position: "absolute", top: 6, left: 6,
    fontSize: 9, fontWeight: 700,
    padding: "2px 7px", borderRadius: 999,
    letterSpacing: "0.05em", textTransform: "uppercase",
    background: isMen ? "#E6F1FB" : "#FBEAF0",
    color: isMen ? "#185FA5" : "#993556",
  };

  return (
    <article style={{
      background: T.surface,
      border: `1px solid ${checked ? T.accent : T.border}`,
      borderRadius: T.radius,
      overflow: "hidden",
      transition: "border-color 0.15s",
    }}>
      <div style={{
        aspectRatio: "3/4",
        background: T.surfaceAlt,
        overflow: "hidden",
        position: "relative",
      }}>
        {imgSrc ? (
          // eslint-disable-next-line @next/next/no-img-element
          <img
            src={imgSrc}
            alt={p.product_title || "product"}
            style={{ width: "100%", height: "100%", objectFit: "cover", display: "block" }}
          />
        ) : (
          <div style={{
            width: "100%", height: "100%",
            display: "flex", alignItems: "center",
            justifyContent: "center",
            fontSize: 26, color: T.textFaint, fontWeight: 300,
          }}>
            {isMen ? "M" : "W"}
          </div>
        )}
        <div style={chipStyle}>{p.gender}</div>
      </div>

      <div style={{ padding: "7px 8px 9px" }}>
        <div style={{
          fontSize: 11, fontWeight: 500, color: T.text,
          lineHeight: 1.3, minHeight: 28,
          display: "-webkit-box",
          WebkitLineClamp: 2,
          WebkitBoxOrient: "vertical",
          overflow: "hidden",
        }}>
          {p.product_title || "Untitled"}
        </div>
        <div style={{ fontSize: 10, color: T.textMuted, marginTop: 3 }}>
          {p.sleeve} · {p.class_name}
        </div>

        <div style={{
          display: "flex", alignItems: "center",
          justifyContent: "space-between",
          marginTop: 7, paddingTop: 7,
          borderTop: `1px solid ${T.border}`,
        }}>
          <label style={{
            display: "flex", alignItems: "center",
            gap: 5, fontSize: 10, color: T.textMuted, cursor: "pointer",
          }}>
            <input
              type="checkbox"
              checked={checked}
              onChange={(e) => onCheck(e.target.checked)}
              style={{ width: 12, height: 12, cursor: "pointer", accentColor: T.accent }}
            />
            Batch
          </label>
          <button
            onClick={onPredict}
            style={{
              fontSize: 10, padding: "3px 10px",
              borderRadius: T.radiusPill,
              border: `1px solid ${T.borderStrong}`,
              background: "transparent", color: T.text,
              cursor: "pointer", fontFamily: "inherit",
            }}
          >
            Predict
          </button>
        </div>
      </div>
    </article>
  );
}

function ResultRow({ label, value, conf }: {
  label: string; value: string | null; conf: number | null;
}) {
  return (
    <div style={{ marginTop: 10 }}>
      <div style={{
        fontSize: 10, color: T.textFaint, fontWeight: 600,
        textTransform: "uppercase", letterSpacing: "0.06em",
      }}>
        {label}
      </div>
      <div style={{
        fontSize: 18, fontWeight: 600, color: T.text,
        marginTop: 2, display: "flex", alignItems: "baseline", gap: 6,
      }}>
        {value || "—"}
        <span style={{ fontSize: 11, fontWeight: 400, color: T.textMuted }}>{pct(conf)}</span>
      </div>
    </div>
  );
}

function StatusBadge({ status }: { status: "success" | "error" }) {
  const ok = status === "success";
  return (
    <span style={{
      fontSize: 10, fontWeight: 500,
      padding: "2px 9px", borderRadius: T.radiusPill,
      background: ok ? T.successBg : T.dangerBg,
      color: ok ? T.success : T.danger,
    }}>
      {status}
    </span>
  );
}
