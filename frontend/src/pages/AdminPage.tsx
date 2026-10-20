import { useEffect, useState } from "react";
import type { AppLang, User } from "../types";
import { i18n } from "../i18n";
import { api, type AdminOverview, type AdminUserRow, type ApiContentReport, type ReportStatus } from "../lib/api";

interface Props {
  lang: AppLang;
  currentUser: User | null;
  onBack: () => void;
}

const STATUS_OPTIONS: ReportStatus[] = ["pending", "reviewing", "resolved", "dismissed"];

export default function AdminPage({ lang, currentUser, onBack }: Props) {
  const t = i18n[lang];
  const [overview, setOverview] = useState<AdminOverview | null>(null);
  const [users, setUsers] = useState<AdminUserRow[]>([]);
  const [reports, setReports] = useState<ApiContentReport[]>([]);
  const [filter, setFilter] = useState<ReportStatus | "">("pending");
  const [selectedId, setSelectedId] = useState<number | null>(null);
  const [notes, setNotes] = useState("");
  const [status, setStatus] = useState<ReportStatus>("pending");
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");

  const statusLabel = (value: ReportStatus) => ({
    pending: t.adminPending,
    reviewing: t.adminReviewing,
    resolved: t.adminResolved,
    dismissed: t.adminDismissed,
  }[value]);

  useEffect(() => {
    if (!currentUser?.isStaff) return;
    setLoading(true);
    setError("");
    Promise.all([
      api.adminOverview(),
      api.adminUsers(),
      api.adminReports(filter || undefined),
    ])
      .then(([nextOverview, nextUsers, nextReports]) => {
        setOverview(nextOverview);
        setUsers(nextUsers);
        setReports(nextReports);
        if (nextReports.length) {
          setSelectedId(nextReports[0].id);
          setNotes(nextReports[0].admin_notes);
          setStatus(nextReports[0].status);
        } else {
          setSelectedId(null);
        }
      })
      .catch(caught => setError(caught instanceof Error ? caught.message : "Could not load admin data"))
      .finally(() => setLoading(false));
  }, [currentUser?.isStaff, filter]);

  const selected = reports.find(report => report.id === selectedId) ?? null;

  useEffect(() => {
    if (!selected) return;
    setNotes(selected.admin_notes);
    setStatus(selected.status);
  }, [selected?.id]);

  if (!currentUser?.isStaff) {
    return (
      <div className="flex flex-col items-center justify-center h-full px-6 text-center pb-20 pixel-bg">
        <div className="text-5xl mb-4">🔒</div>
        <h2 className="font-display text-lg font-bold text-foreground mb-2">{t.adminOnly}</h2>
        <p className="text-muted-foreground text-sm mb-6">{lang === "th" ? "ต้องใช้บัญชีผู้ดูแลระบบ (staff)" : "Sign in with a staff account to open the admin dashboard."}</p>
        <button onClick={onBack} className="px-6 py-3 text-sm font-bold font-display chip-btn-outline">{t.back}</button>
      </div>
    );
  }

  const saveReport = async () => {
    if (!selected) return;
    setSaving(true);
    setError("");
    try {
      const updated = await api.updateAdminReport(selected.id, { status, admin_notes: notes });
      setReports(current => current.map(report => report.id === updated.id ? updated : report));
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Could not update report");
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="page-shell bg-background pixel-bg">
      <div className="page-container flex items-center gap-3 px-4 md:px-6 lg:px-8 page-header pb-4 shrink-0 page-header-bar">
        <button onClick={onBack} className="w-8 h-8 flex items-center justify-center font-display text-muted-foreground chip-btn-outline">←</button>
        <div>
          <h1 className="font-display text-lg font-bold page-title">{t.adminTitle}</h1>
          <p className="text-xs text-muted-foreground font-mono">{currentUser.name}</p>
        </div>
      </div>

      <div className="page-scroll scroll-end-buffer px-4 md:px-6 lg:px-8 py-4 space-y-4 page-container max-w-5xl w-full">
        {loading && <p className="text-sm text-muted-foreground">{t.loading}</p>}
        {error && <p className="text-xs text-danger">{error}</p>}

        {overview && (
          <div className="grid grid-cols-2 md:grid-cols-4 gap-2.5 md:gap-3">
            {[
              { label: t.adminUsers, value: overview.users.total, sub: `${overview.users.personal} ${t.personal} · ${overview.users.business} ${t.business}` },
              { label: t.adminListings, value: overview.listings.total, sub: `${overview.listings.active} ${t.available}` },
              { label: t.adminReports, value: overview.reports.total, sub: `${overview.reports.pending} ${t.adminPending}` },
              { label: t.adminStaff, value: overview.users.staff, sub: `${overview.messaging.deals_completed} ${t.adminDealsCompleted}` },
            ].map(kpi => (
              <div key={kpi.label} className="p-4 panel-card">
                <p className="text-2xl font-bold font-mono text-primary">{kpi.value}</p>
                <p className="font-display text-xs text-muted-foreground mt-0.5">{kpi.label}</p>
                <p className="text-[10px] text-muted-foreground mt-1">{kpi.sub}</p>
              </div>
            ))}
          </div>
        )}

        {users.length > 0 && (
          <div className="panel-card overflow-hidden">
            <div className="px-4 py-3 panel-divider">
              <h2 className="font-display font-semibold text-sm text-foreground">{t.adminUsers}</h2>
            </div>
            <div className="max-h-64 overflow-y-auto">
              {users.map(user => (
                <div key={user.id} className="px-4 py-2.5 panel-divider text-xs font-mono flex flex-wrap items-center gap-x-3 gap-y-1">
                  <span className="font-display font-semibold text-foreground">{user.display_name}</span>
                  <span className="text-muted-foreground truncate">{user.email}</span>
                  <span className="text-muted-foreground">{user.role}</span>
                  {user.is_staff && <span className="text-primary font-display">{t.adminStaff}</span>}
                  <span className="text-muted-foreground ml-auto">{user.date_joined.slice(0, 10)}</span>
                </div>
              ))}
            </div>
          </div>
        )}

        {overview && (
          <div className="panel-card p-4 grid grid-cols-2 md:grid-cols-3 gap-3 text-xs font-mono">
            <div><span className="text-muted-foreground">{t.adminConversations}: </span>{overview.messaging.conversations}</div>
            <div><span className="text-muted-foreground">{t.adminMessages}: </span>{overview.messaging.messages}</div>
            <div><span className="text-muted-foreground">{t.adminOffers}: </span>{overview.messaging.offers}</div>
            <div><span className="text-muted-foreground">{t.adminDealsActive}: </span>{overview.messaging.deals_active}</div>
            <div><span className="text-muted-foreground">{t.adminReviewsCount}: </span>{overview.messaging.reviews}</div>
            <div><span className="text-muted-foreground">{t.adminResolved}: </span>{overview.reports.resolved}</div>
          </div>
        )}

        <div className="panel-card overflow-hidden">
          <div className="flex flex-wrap items-center gap-2 px-4 py-3 panel-divider">
            <h2 className="font-display font-semibold text-sm text-foreground flex-1">{t.adminReports}</h2>
            <select value={filter} onChange={event => setFilter(event.target.value as ReportStatus | "")}
              className="text-xs px-2 py-1.5 bg-background border border-border rounded font-display">
              <option value="">{lang === "th" ? "ทั้งหมด" : "All"}</option>
              {STATUS_OPTIONS.map(option => (
                <option key={option} value={option}>{statusLabel(option)}</option>
              ))}
            </select>
          </div>

          {!reports.length && !loading ? (
            <p className="px-4 py-6 text-sm text-muted-foreground">{t.adminNoReports}</p>
          ) : (
            <div className="md:grid md:grid-cols-2 md:divide-x" style={{ borderColor: "var(--color-border)" }}>
              <div className="max-h-80 md:max-h-[28rem] overflow-y-auto">
                {reports.map(report => (
                  <button key={report.id} type="button" onClick={() => setSelectedId(report.id)}
                    className={`w-full text-left px-4 py-3 panel-divider transition-colors ${selectedId === report.id ? "bg-[var(--color-row-hover)]" : "hover:bg-[var(--color-row-hover)]"}`}>
                    <div className="flex items-center justify-between gap-2">
                      <span className="font-display text-xs font-semibold text-foreground truncate">#{report.id} · {report.target?.label ?? report.category}</span>
                      <span className="text-[10px] font-mono text-muted-foreground shrink-0">{statusLabel(report.status)}</span>
                    </div>
                    <p className="text-[10px] text-muted-foreground mt-1 truncate">{report.reporter.display_name} · {report.reason}</p>
                  </button>
                ))}
              </div>
              <div className="p-4 min-h-[12rem]">
                {selected ? (
                  <div className="space-y-3">
                    <div>
                      <p className="font-display text-sm font-bold text-foreground">{selected.target?.label}</p>
                      <p className="text-xs text-muted-foreground mt-1">{selected.reporter.display_name} ({selected.reporter.email})</p>
                      <p className="text-xs text-muted-foreground">{selected.details || "—"}</p>
                    </div>
                    <label className="block">
                      <span className="font-display text-xs text-muted-foreground">{t.adminUpdateStatus}</span>
                      <select value={status} onChange={event => setStatus(event.target.value as ReportStatus)}
                        className="mt-1 w-full px-3 py-2 text-sm bg-background border border-border rounded font-display">
                        {STATUS_OPTIONS.map(option => (
                          <option key={option} value={option}>{statusLabel(option)}</option>
                        ))}
                      </select>
                    </label>
                    <label className="block">
                      <span className="font-display text-xs text-muted-foreground">{t.adminNotes}</span>
                      <textarea value={notes} onChange={event => setNotes(event.target.value)} rows={3} maxLength={2000}
                        className="mt-1 w-full px-3 py-2 text-sm bg-background border border-border rounded resize-none font-display" />
                    </label>
                    <button type="button" onClick={() => void saveReport()} disabled={saving}
                      className="w-full py-3 text-sm font-bold font-display btn-primary" style={{ borderRadius: 4 }}>
                      {saving ? t.loading : t.save}
                    </button>
                  </div>
                ) : null}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
