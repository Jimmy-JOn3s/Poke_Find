import { useEffect, useState } from "react";
import type { AppLang, User } from "../types";
import { i18n } from "../i18n";
import { api, resolveMediaUrl, type AdminCompletedDeal, type AdminMarketIntelligence, type AdminOpenDeal, type AdminOverview, type AdminReportListingSnapshot, type AdminReportAction, type AdminUserRow, type ApiAdminVerification, type ApiContentReport, type ReportStatus } from "../lib/api";
import { formatMoney } from "../lib/money";

interface Props {
  lang: AppLang;
  currentUser: User | null;
  onBack: () => void;
  onOpenListing: (listingId: number) => Promise<void>;
  onOpenProfile?: (userId: number) => void;
}

const STATUS_OPTIONS: ReportStatus[] = ["pending", "reviewing", "resolved", "dismissed"];

function listingImageUrl(listing: AdminReportListingSnapshot): string | undefined {
  if (listing.photo) return resolveMediaUrl(listing.photo);
  return listing.image_url || undefined;
}

function dealImageUrl(deal: AdminCompletedDeal): string | undefined {
  if (deal.listing_photo) return resolveMediaUrl(deal.listing_photo);
  return deal.listing_image_url || undefined;
}

function dealCardName(deal: AdminCompletedDeal): string {
  return deal.card_name || deal.listing_product_name || "Card";
}

function reportListingId(report: ApiContentReport): number | null {
  if (report.target_detail?.listing) return report.target_detail.listing.id;
  if (report.target?.kind === "listing") return report.target.id;
  return null;
}

function deactivateTargetLabel(report: ApiContentReport): string | null {
  if (report.target_detail?.user) return report.target_detail.user.display_name;
  if (report.target_detail?.listing?.seller) return report.target_detail.listing.seller.display_name;
  if (report.target_detail?.message) return report.target_detail.message.author_name;
  return null;
}

export default function AdminPage({ lang, currentUser, onBack, onOpenListing, onOpenProfile }: Props) {
  const t = i18n[lang];
  const [overview, setOverview] = useState<AdminOverview | null>(null);
  const [market, setMarket] = useState<AdminMarketIntelligence | null>(null);
  const [openDeals, setOpenDeals] = useState<AdminOpenDeal[]>([]);
  const [dealActionId, setDealActionId] = useState<number | null>(null);
  const [expiringDeals, setExpiringDeals] = useState(false);
  const [users, setUsers] = useState<AdminUserRow[]>([]);
  const [reports, setReports] = useState<ApiContentReport[]>([]);
  const [filter, setFilter] = useState<ReportStatus | "">("pending");
  const [selectedId, setSelectedId] = useState<number | null>(null);
  const [notes, setNotes] = useState("");
  const [status, setStatus] = useState<ReportStatus>("pending");
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");
  const [verifications, setVerifications] = useState<ApiAdminVerification[]>([]);
  const [verificationFilter, setVerificationFilter] = useState<"" | "pending" | "approved" | "rejected">("pending");
  const [selectedVerificationId, setSelectedVerificationId] = useState<number | null>(null);
  const [verificationNotes, setVerificationNotes] = useState("");
  const [rejectionReason, setRejectionReason] = useState("");
  const [idPreviewUrl, setIdPreviewUrl] = useState<string | null>(null);
  const [selfiePreviewUrl, setSelfiePreviewUrl] = useState<string | null>(null);
  const [verificationSaving, setVerificationSaving] = useState(false);
  const [openingListingId, setOpeningListingId] = useState<number | null>(null);
  const [actionLoading, setActionLoading] = useState<AdminReportAction | null>(null);

  const openListing = async (listingId: number) => {
    setOpeningListingId(listingId);
    setError("");
    try {
      await onOpenListing(listingId);
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Could not open listing");
    } finally {
      setOpeningListingId(null);
    }
  };

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
      api.adminMarketIntelligence(),
      api.adminUsers(),
      api.adminReports(filter || undefined),
      api.adminVerifications(verificationFilter || undefined),
      api.adminOpenDeals(),
    ])
      .then(([nextOverview, nextMarket, nextUsers, nextReports, nextVerifications, nextOpenDeals]) => {
        setOverview(nextOverview);
        setMarket(nextMarket);
        setUsers(nextUsers);
        setReports(nextReports);
        setVerifications(nextVerifications);
        setOpenDeals(nextOpenDeals);
        if (nextVerifications.length) {
          setSelectedVerificationId(nextVerifications[0].id);
          setVerificationNotes(nextVerifications[0].admin_notes);
          setRejectionReason(nextVerifications[0].rejection_reason);
        } else {
          setSelectedVerificationId(null);
        }
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
  }, [currentUser?.isStaff, filter, verificationFilter]);

  const selected = reports.find(report => report.id === selectedId) ?? null;
  const primaryListingId = selected ? reportListingId(selected) : null;
  const canHideListing = Boolean(selected?.target_detail?.listing);
  const canRemoveMessage = selected?.category === "message";
  const deactivateLabel = selected ? deactivateTargetLabel(selected) : null;
  const canDeactivateUser = Boolean(deactivateLabel);

  useEffect(() => {
    if (!selected) return;
    setNotes(selected.admin_notes);
    setStatus(selected.status);
  }, [selected?.id]);

  const selectedVerification = verifications.find(item => item.id === selectedVerificationId) ?? null;

  useEffect(() => {
    if (!selectedVerification) {
      setIdPreviewUrl(null);
      setSelfiePreviewUrl(null);
      return;
    }
    setVerificationNotes(selectedVerification.admin_notes);
    setRejectionReason(selectedVerification.rejection_reason);
    let cancelled = false;
    const urls: string[] = [];
    void (async () => {
      try {
        const idBlob = await api.adminVerificationFileBlob(selectedVerification.id, "id_document");
        if (cancelled) return;
        const idUrl = URL.createObjectURL(idBlob);
        urls.push(idUrl);
        setIdPreviewUrl(idUrl);
        if (selectedVerification.has_selfie) {
          const selfieBlob = await api.adminVerificationFileBlob(selectedVerification.id, "selfie");
          if (cancelled) return;
          const selfieUrl = URL.createObjectURL(selfieBlob);
          urls.push(selfieUrl);
          setSelfiePreviewUrl(selfieUrl);
        } else {
          setSelfiePreviewUrl(null);
        }
      } catch {
        if (!cancelled) setError(lang === "th" ? "โหลดเอกสารไม่สำเร็จ" : "Could not load documents");
      }
    })();
    return () => {
      cancelled = true;
      urls.forEach(url => URL.revokeObjectURL(url));
    };
  }, [selectedVerification?.id, lang]);

  const reviewVerification = async (action: "approve" | "reject") => {
    if (!selectedVerification) return;
    setVerificationSaving(true);
    setError("");
    try {
      const updated = await api.reviewAdminVerification(selectedVerification.id, {
        action,
        admin_notes: verificationNotes,
        rejection_reason: action === "reject" ? rejectionReason : undefined,
      });
      setVerifications(current => current.map(item => item.id === updated.id ? updated : item));
      const reloaded = await api.adminVerifications(verificationFilter || undefined);
      setVerifications(reloaded);
      setOverview(await api.adminOverview());
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Could not review submission");
    } finally {
      setVerificationSaving(false);
    }
  };

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

  const forceCancelDeal = async (dealId: number) => {
    setDealActionId(dealId);
    setError("");
    try {
      await api.adminForceCancelDeal(dealId);
      setOpenDeals(await api.adminOpenDeals());
      setOverview(await api.adminOverview());
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Could not cancel deal");
    } finally {
      setDealActionId(null);
    }
  };

  const releaseStaleDeals = async () => {
    setExpiringDeals(true);
    setError("");
    try {
      await api.adminExpireStaleDeals();
      setOpenDeals(await api.adminOpenDeals());
      setOverview(await api.adminOverview());
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Could not release stale deals");
    } finally {
      setExpiringDeals(false);
    }
  };

  const runReportAction = async (action: AdminReportAction) => {
    if (!selected) return;
    setActionLoading(action);
    setError("");
    try {
      const result = await api.adminReportAction(selected.id, {
        action,
        mark_resolved: true,
        admin_notes: notes.trim() || undefined,
      });
      setReports(current => current.map(report => report.id === result.report.id ? result.report : report));
      setNotes(result.report.admin_notes);
      setStatus(result.report.status);
      setOverview(await api.adminOverview());
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Could not run action");
    } finally {
      setActionLoading(null);
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
              { label: t.adminReports, value: overview.reports.total, sub: `${overview.reports.pending} ${t.adminPending} · ${overview.verifications?.pending ?? 0} ${t.adminVerifications}` },
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

        {market && (
          <div className="panel-card overflow-hidden">
            <div className="px-4 py-3 panel-divider">
              <h2 className="font-display font-semibold text-sm text-foreground">{t.adminMarketIntelligence}</h2>
              <p className="text-[10px] text-muted-foreground font-mono mt-1">
                {market.completed_deals} {t.adminDealsCompleted}
                {Object.keys(market.revenue_by_currency).length > 0 && (
                  <> · {Object.entries(market.revenue_by_currency).map(([code, amount]) => `${code} ${amount}`).join(" · ")}</>
                )}
              </p>
            </div>
            <div className="p-4 grid md:grid-cols-2 gap-4">
              <div>
                <h3 className="font-display text-xs font-semibold text-foreground mb-2">{t.adminTopTradedCards}</h3>
                {!market.top_cards.length ? (
                  <p className="text-xs text-muted-foreground">{t.adminNoTransactions}</p>
                ) : (
                  <ul className="space-y-2 max-h-56 overflow-y-auto">
                    {market.top_cards.map((card, index) => (
                      <li key={`${card.name}-${index}`} className="flex items-center gap-2 text-xs font-mono">
                        <span className="text-muted-foreground w-4">{index + 1}</span>
                        <div className="min-w-0 flex-1">
                          <p className="font-display font-semibold text-foreground truncate">{card.name}</p>
                          <p className="text-[10px] text-muted-foreground truncate">
                            {card.card_set || "—"} · {card.sold} {lang === "th" ? "ครั้ง" : "sales"}
                          </p>
                          <p className="text-[10px] text-muted-foreground">
                            {t.adminAvgSalePrice}: {formatMoney(
                              Number(card.avg_price ?? (card.sold ? Number(card.revenue) / card.sold : 0)),
                              card.currency,
                              lang,
                            )}
                          </p>
                        </div>
                        <span className="text-primary font-semibold shrink-0 text-right">
                          <span className="block">{formatMoney(Number(card.revenue), card.currency, lang)}</span>
                          <span className="text-[9px] text-muted-foreground font-normal">{lang === "th" ? "รวม" : "total"}</span>
                        </span>
                      </li>
                    ))}
                  </ul>
                )}
              </div>
              <div>
                <h3 className="font-display text-xs font-semibold text-foreground mb-2">{t.adminRecentTransactions}</h3>
                {!market.recent_transactions.length ? (
                  <p className="text-xs text-muted-foreground">{t.adminNoTransactions}</p>
                ) : (
                  <ul className="space-y-2 max-h-56 overflow-y-auto">
                    {market.recent_transactions.map(deal => (
                      <li key={deal.id}>
                        <button
                          type="button"
                          onClick={() => void openListing(deal.listing_id)}
                          className="w-full flex gap-3 p-2 rounded border border-border text-left hover:bg-[var(--color-row-hover)] transition-colors"
                        >
                          {dealImageUrl(deal) ? (
                            <img src={dealImageUrl(deal)} alt="" className="w-10 h-14 object-contain rounded shrink-0" />
                          ) : (
                            <div className="w-10 h-14 shrink-0 rounded bg-muted flex items-center justify-center text-sm">🃏</div>
                          )}
                          <div className="min-w-0 flex-1 text-[10px] font-mono">
                            <p className="font-display text-xs font-semibold text-foreground truncate">{dealCardName(deal)}</p>
                            <p className="text-success font-semibold">{formatMoney(Number(deal.final_price), deal.currency, lang)}</p>
                            <p className="text-muted-foreground truncate">
                              {deal.buyer_name} → {deal.seller_name}
                              {deal.completed_at ? ` · ${deal.completed_at.slice(0, 10)}` : ""}
                            </p>
                          </div>
                        </button>
                      </li>
                    ))}
                  </ul>
                )}
              </div>
            </div>
          </div>
        )}

        {overview && (
          <div className="panel-card overflow-hidden">
            <div className="flex flex-wrap items-center gap-2 px-4 py-3 panel-divider">
              <h2 className="font-display font-semibold text-sm text-foreground flex-1">{t.adminStuckDeals}</h2>
              <button
                type="button"
                disabled={expiringDeals}
                onClick={() => void releaseStaleDeals()}
                className="text-xs px-2 py-1.5 chip-btn-outline font-display"
              >
                {expiringDeals ? t.loading : t.adminReleaseStaleDeals}
              </button>
            </div>
            {!openDeals.length ? (
              <p className="px-4 pb-4 text-xs text-muted-foreground">{lang === "th" ? "ไม่มีดีลค้าง" : "No open deals"}</p>
            ) : (
            <ul className="max-h-56 overflow-y-auto px-4 pb-3 space-y-2">
              {openDeals.map(deal => (
                <li key={deal.id} className="panel-card p-2 text-[10px] font-mono space-y-1">
                  <p className="font-display text-xs font-semibold text-foreground truncate">
                    {deal.card_name || deal.listing_name}
                    {deal.is_stale && (
                      <span className="ml-1 text-danger font-mono text-[9px]"> · {t.adminStaleBadge}</span>
                    )}
                  </p>
                  <p className="text-muted-foreground truncate">
                    {formatMoney(Number(deal.final_price), deal.currency, lang)} · {deal.buyer_name} → {deal.seller_name}
                  </p>
                  <p className="text-muted-foreground">
                    {deal.buyer_confirmed || deal.seller_confirmed
                      ? (lang === "th" ? "ยืนยันแล้วบางส่วน" : "Partially confirmed")
                      : (lang === "th" ? "ยังไม่มีใครยืนยัน" : "No confirmations yet")}
                  </p>
                  {deal.stale_outcome && (
                    <p className={deal.stale_outcome === "await_buyer" ? "text-danger" : "text-muted-foreground"}>
                      {deal.stale_outcome === "complete"
                        ? t.adminStaleWillComplete
                        : deal.stale_outcome === "await_buyer"
                          ? t.adminStaleAwaitBuyer
                          : t.adminStaleWillCancel}
                    </p>
                  )}
                  <button
                    type="button"
                    disabled={dealActionId !== null}
                    onClick={() => void forceCancelDeal(deal.id)}
                    className="w-full py-1.5 text-xs font-bold btn-danger-outline"
                    style={{ borderRadius: 4 }}
                  >
                    {dealActionId === deal.id ? t.loading : t.adminForceCancelDeal}
                  </button>
                </li>
              ))}
            </ul>
            )}
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
            <h2 className="font-display font-semibold text-sm text-foreground flex-1">{t.adminVerifications}</h2>
            <select value={verificationFilter} onChange={event => setVerificationFilter(event.target.value as typeof verificationFilter)}
              className="text-xs px-2 py-1.5 bg-background border border-border rounded font-display">
              <option value="">{lang === "th" ? "ทั้งหมด" : "All"}</option>
              <option value="pending">{t.adminPending}</option>
              <option value="approved">{t.verified}</option>
              <option value="rejected">{t.verificationRejected}</option>
            </select>
          </div>
          {!verifications.length && !loading ? (
            <p className="px-4 py-6 text-sm text-muted-foreground">{t.adminNoVerifications}</p>
          ) : (
            <div className="md:grid md:grid-cols-2 md:divide-x" style={{ borderColor: "var(--color-border)" }}>
              <div className="max-h-80 overflow-y-auto">
                {verifications.map(item => (
                  <button key={item.id} type="button" onClick={() => setSelectedVerificationId(item.id)}
                    className={`w-full text-left px-4 py-3 panel-divider transition-colors ${selectedVerificationId === item.id ? "bg-[var(--color-row-hover)]" : "hover:bg-[var(--color-row-hover)]"}`}>
                    <p className="font-display text-xs font-semibold text-foreground truncate">
                      #{item.id} · {item.user_display_name}
                    </p>
                    <p className="text-[10px] text-muted-foreground mt-1 truncate">
                      {item.user_email} · {item.document_type === "id" ? t.idCard : t.passport} · {item.status}
                    </p>
                  </button>
                ))}
              </div>
              <div className="p-4 space-y-3 min-h-[12rem]">
                {selectedVerification ? (
                  <>
                    {idPreviewUrl && (
                      <img src={idPreviewUrl} alt="" className="max-h-40 w-full object-contain rounded border border-border" />
                    )}
                    {selfiePreviewUrl && (
                      <img src={selfiePreviewUrl} alt="" className="max-h-32 w-full object-contain rounded border border-border" />
                    )}
                    <label className="block">
                      <span className="font-display text-xs text-muted-foreground">{t.adminNotes}</span>
                      <textarea value={verificationNotes} onChange={event => setVerificationNotes(event.target.value)} rows={2} maxLength={2000}
                        className="mt-1 w-full px-3 py-2 text-sm bg-background border border-border rounded resize-none font-display" />
                    </label>
                    {selectedVerification.status === "pending" && (
                      <>
                        <label className="block">
                          <span className="font-display text-xs text-muted-foreground">{t.adminRejectionReason}</span>
                          <textarea value={rejectionReason} onChange={event => setRejectionReason(event.target.value)} rows={2} maxLength={1000}
                            className="mt-1 w-full px-3 py-2 text-sm bg-background border border-border rounded resize-none font-display" />
                        </label>
                        <div className="flex gap-2">
                          <button type="button" disabled={verificationSaving} onClick={() => void reviewVerification("approve")}
                            className="flex-1 py-2 text-xs font-bold btn-primary" style={{ borderRadius: 4 }}>
                            {verificationSaving ? t.loading : t.adminApprove}
                          </button>
                          <button type="button" disabled={verificationSaving || !rejectionReason.trim()} onClick={() => void reviewVerification("reject")}
                            className="flex-1 py-2 text-xs font-bold btn-danger-outline" style={{ borderRadius: 4 }}>
                            {verificationSaving ? t.loading : t.adminReject}
                          </button>
                        </div>
                      </>
                    )}
                  </>
                ) : null}
              </div>
            </div>
          )}
        </div>

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
              <div className="p-4 min-h-[12rem] max-h-[32rem] overflow-y-auto">
                {selected ? (
                  <div className="space-y-3">
                    <div>
                      <p className="font-display text-sm font-bold text-foreground">{selected.target?.label}</p>
                      <p className="text-xs text-muted-foreground mt-1">{selected.reporter.display_name} ({selected.reporter.email})</p>
                      <p className="text-[10px] text-muted-foreground font-mono mt-1">
                        {selected.category} · {selected.reason} · {selected.created_at.slice(0, 16).replace("T", " ")}
                      </p>
                      <p className="text-xs text-muted-foreground mt-1">{selected.details || "—"}</p>
                      {primaryListingId != null && (
                        <button
                          type="button"
                          disabled={openingListingId === primaryListingId}
                          onClick={() => void openListing(primaryListingId)}
                          className="mt-2 w-full py-2 text-xs font-bold font-display btn-primary"
                          style={{ borderRadius: 4 }}
                        >
                          {openingListingId === primaryListingId ? t.loading : t.adminOpenListing}
                        </button>
                      )}
                    </div>

                    {selected.target_detail?.listing && (
                      <button
                        type="button"
                        onClick={() => void openListing(selected.target_detail!.listing!.id)}
                        className="panel-card p-3 space-y-2 w-full text-left hover:bg-[var(--color-row-hover)] transition-colors"
                      >
                        <div className="flex items-center justify-between gap-2">
                          <p className="font-display text-xs font-semibold text-foreground">{t.adminReportedListing}</p>
                          <span className="text-[10px] text-primary font-display">{t.adminViewListing} →</span>
                        </div>
                        <div className="flex gap-3">
                          {listingImageUrl(selected.target_detail.listing) ? (
                            <img
                              src={listingImageUrl(selected.target_detail.listing)}
                              alt=""
                              className="w-16 h-22 object-contain rounded border border-border shrink-0"
                            />
                          ) : (
                            <div className="w-16 h-22 shrink-0 rounded border border-border bg-muted flex items-center justify-center text-lg">🃏</div>
                          )}
                          <div className="min-w-0 text-xs">
                            <p className="font-display font-semibold text-foreground truncate">{selected.target_detail.listing.product_name}</p>
                            <p className="text-muted-foreground truncate">
                              {selected.target_detail.listing.set_name} · #{selected.target_detail.listing.card_number}
                            </p>
                            <p className="text-primary font-mono font-semibold mt-0.5">
                              {formatMoney(Number(selected.target_detail.listing.asking_price), selected.target_detail.listing.currency, lang)}
                            </p>
                            <p className="text-muted-foreground">
                              {selected.target_detail.listing.condition} · {selected.target_detail.listing.status} · {selected.target_detail.listing.seller.display_name}
                            </p>
                          </div>
                        </div>
                      </button>
                    )}

                    {selected.target_detail?.message && (
                      <div className="panel-card p-3 space-y-1">
                        <p className="font-display text-xs font-semibold text-foreground">{t.adminReportedMessage}</p>
                        <p className="text-[10px] text-muted-foreground font-mono">
                          {selected.target_detail.message.author_name} · {selected.target_detail.message.created_at.slice(0, 16).replace("T", " ")}
                        </p>
                        <p className="text-xs text-foreground whitespace-pre-wrap break-words">{selected.target_detail.message.body}</p>
                      </div>
                    )}

                    {selected.target_detail?.user && (
                      <div className="panel-card p-3 space-y-2 text-xs">
                        <p className="font-display text-xs font-semibold text-foreground">{t.adminReportedUser}</p>
                        <p className="font-display font-semibold">{selected.target_detail.user.display_name}</p>
                        <p className="text-muted-foreground">{selected.target_detail.user.email} · {selected.target_detail.user.role}</p>
                        <p className="text-muted-foreground font-mono">#{selected.target_detail.user.id} · {selected.target_detail.user.date_joined.slice(0, 10)}</p>
                        {onOpenProfile && (
                          <button
                            type="button"
                            onClick={() => onOpenProfile(selected.target_detail!.user!.id)}
                            className="w-full py-2 text-xs font-bold font-display chip-btn-outline"
                          >
                            {t.adminViewProfile}
                          </button>
                        )}
                      </div>
                    )}

                    {(canHideListing || canDeactivateUser || canRemoveMessage) && (
                      <div className="panel-card p-3 space-y-2">
                        <p className="font-display text-xs font-semibold text-foreground">{t.adminModerationActions}</p>
                        <p className="text-[10px] text-muted-foreground">
                          {lang === "th"
                            ? "ดำเนินการแล้วจะตั้งสถานะเป็น “แก้ไขแล้ว” โดยอัตโนมัติ"
                            : "Actions automatically mark the report resolved."}
                        </p>
                        <div className="flex flex-col gap-2">
                          {canHideListing && (
                            <button
                              type="button"
                              disabled={actionLoading !== null}
                              onClick={() => void runReportAction("hide_listing")}
                              className="w-full py-2 text-xs font-bold font-display btn-danger-outline"
                              style={{ borderRadius: 4 }}
                            >
                              {actionLoading === "hide_listing" ? t.loading : t.adminActionHideListing}
                            </button>
                          )}
                          {canDeactivateUser && (
                            <button
                              type="button"
                              disabled={actionLoading !== null}
                              onClick={() => void runReportAction("deactivate_user")}
                              className="w-full py-2 text-xs font-bold font-display btn-danger-outline"
                              style={{ borderRadius: 4 }}
                            >
                              {actionLoading === "deactivate_user"
                                ? t.loading
                                : `${t.adminActionDeactivateUser}${deactivateLabel ? ` (${deactivateLabel})` : ""}`}
                            </button>
                          )}
                          {canRemoveMessage && (
                            <button
                              type="button"
                              disabled={actionLoading !== null}
                              onClick={() => void runReportAction("remove_message")}
                              className="w-full py-2 text-xs font-bold font-display btn-danger-outline"
                              style={{ borderRadius: 4 }}
                            >
                              {actionLoading === "remove_message" ? t.loading : t.adminActionRemoveMessage}
                            </button>
                          )}
                        </div>
                      </div>
                    )}

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
