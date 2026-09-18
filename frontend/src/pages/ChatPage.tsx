import { useEffect, useState } from "react";
import type { AppLang, ReviewContext, User } from "../types";
import { api, type ApiConversation, type ApiDeal, type ApiMessage, type ApiOffer } from "../lib/api";
import { formatMoney } from "../lib/money";
import ReviewPromptModal from "../components/ReviewPromptModal";


interface Props {
  initialConversationId: number | null;
  lang: AppLang;
  currentUser: User | null;
  isAuthenticated: boolean;
  onSignIn: () => void;
  onLeaveReview: (context: ReviewContext) => void;
}


export default function ChatPage({ initialConversationId, lang, currentUser, isAuthenticated, onSignIn, onLeaveReview }: Props) {
  const copy = lang === "th" ? {
    title: "ข้อความ", empty: "ยังไม่มีการสนทนา", signIn: "เข้าสู่ระบบเพื่อดูข้อความ",
    type: "พิมพ์ข้อความ...", send: "ส่ง", offer: "เสนอราคา", accept: "ยอมรับ",
    decline: "ปฏิเสธ", complete: "ยืนยันว่าซื้อขายสำเร็จ", retry: "ลองอีกครั้ง",
    reviewBanner: "ทิ้งรีวิวให้", leaveReview: "เขียนรีวิว",
  } : {
    title: "Messages", empty: "No conversations yet", signIn: "Sign in to view messages",
    type: "Type a message...", send: "Send", offer: "Make offer", accept: "Accept",
    decline: "Decline", complete: "Confirm completed trade", retry: "Try again",
    reviewBanner: "Leave a review for", leaveReview: "Leave a Review",
  };
  const inbox = lang === "th" ? {
    search: "ค้นหาคนหรือการ์ด", all: "ทั้งหมด", buying: "กำลังซื้อ", selling: "กำลังขาย",
    back: "กลับไปกล่องข้อความ", select: "เลือกการสนทนา", hint: "พูดคุย ตกลงราคา และติดตามการซื้อขายของคุณ",
    noMatch: "ไม่พบการสนทนา", start: "เริ่มพูดคุยจากหน้าประกาศการ์ด", you: "คุณ", first: "เริ่มการสนทนา", loading: "กำลังโหลด…",
  } : {
    search: "Search people or cards", all: "All", buying: "Buying", selling: "Selling",
    back: "Back to inbox", select: "Select a conversation", hint: "Chat, agree on a price, and keep your trades together.",
    noMatch: "No matching conversations", start: "Start a conversation from a card listing.", you: "You", first: "Start the conversation", loading: "Loading…",
  };
  const [search, setSearch] = useState("");
  const [filter, setFilter] = useState<"all" | "buying" | "selling">("all");
  const [sending, setSending] = useState(false);
  const [threadLoading, setThreadLoading] = useState(false);
  const [threads, setThreads] = useState<ApiConversation[]>([]);
  const [activeId, setActiveId] = useState<number | null>(initialConversationId);
  const active = threads.find(thread => thread.id === activeId) ?? null;
  const [messages, setMessages] = useState<ApiMessage[]>([]);
  const [offers, setOffers] = useState<ApiOffer[]>([]);
  const [body, setBody] = useState("");
  const [offerAmount, setOfferAmount] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const [reviewPrompt, setReviewPrompt] = useState<ReviewContext | null>(null);

  const maybePromptReview = (deal: ApiDeal) => {
    if (deal.status !== "completed" || deal.reviewer_has_reviewed === true || !deal.counterparty_id) return;
    setReviewPrompt({
      dealId: deal.id,
      revieweeId: String(deal.counterparty_id),
      revieweeName: deal.counterparty_name || "",
    });
  };

  const confirmCompletion = async () => {
    if (!active?.deal) return;
    try {
      const deal = await api.confirmDeal(active.deal.id);
      await loadThreads();
      maybePromptReview(deal);
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Request failed");
    }
  };

  const loadThreads = async () => {
    if (!isAuthenticated) return;
    setLoading(true); setError("");
    try {
      const result = await api.conversations();
      setThreads(result);
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Request failed");
    } finally { setLoading(false); }
  };

  useEffect(() => {
    void loadThreads();
  }, [isAuthenticated]);
  useEffect(() => {
    setMessages([]); setOffers([]); setBody(""); setOfferAmount(""); setError("");
    if (!active) return;
    // Ignore stale responses if the user switches chats or leaves the page.
    let ignore = false;
    setThreadLoading(true);
    Promise.all([api.messages(active.id), api.offers(active.id)])
      .then(async ([nextMessages, nextOffers]) => {
        if (ignore) return;
        setMessages(nextMessages); setOffers(nextOffers);
        const latest = nextMessages.at(-1);
        if (latest) {
          const updated = await api.markConversationRead(active.id, latest.id);
          if (!ignore) setThreads(items => items.map(item => item.id === updated.id ? updated : item));
        }
      })
      .catch(caught => { if (!ignore) setError(caught instanceof Error ? caught.message : "Request failed"); })
      .finally(() => { if (!ignore) setThreadLoading(false); });
    return () => { ignore = true; };
  }, [active?.id]);

  if (!isAuthenticated) return (
    <div className="flex-1 flex flex-col items-center justify-center text-center px-6 pixel-bg">
      <div className="text-5xl mb-4">💬</div><p className="text-muted-foreground mb-4">{copy.signIn}</p>
      <button onClick={onSignIn} className="btn-primary px-6 py-3 text-sm">{copy.signIn}</button>
    </div>
  );

  const sendMessage = async () => {
    if (!active || !body.trim() || sending) return;
    setSending(true);
    try {
      const message = await api.sendMessage(active.id, body.trim());
      setMessages(items => [...items, message]);
      setBody("");
      setThreads(items => items.map(item => item.id === active.id ? { ...item, latest_message: message } : item));
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Request failed");
    } finally { setSending(false); }
  };

  const makeOffer = async () => {
    if (!active || !offerAmount) return;
    try { const offer = await api.createOffer(active.id, offerAmount, active.listing.currency); setOffers(items => [offer, ...items]); setOfferAmount(""); }
    catch (caught) { setError(caught instanceof Error ? caught.message : "Request failed"); }
  };

  const actOnOffer = async (offer: ApiOffer, action: "accept" | "decline") => {
    try {
      const updated = action === "accept" ? await api.acceptOffer(offer.id) : await api.declineOffer(offer.id);
      setOffers(items => items.map(item => item.id === updated.id ? updated : item));
      await loadThreads();
    } catch (caught) { setError(caught instanceof Error ? caught.message : "Request failed"); }
  };

  const threadLabel = (thread: ApiConversation) =>
    thread.buyer.id === Number(currentUser?.id) ? thread.seller.display_name : thread.buyer.display_name;

  const visibleThreads = threads.filter(thread => {
    const buying = thread.buyer.id === Number(currentUser?.id);
    return (filter === "all" || (filter === "buying" ? buying : !buying))
      && `${threadLabel(thread)} ${thread.listing.product_name}`.toLowerCase().includes(search.toLowerCase());
  }).sort((a, b) => Date.parse(b.latest_message?.created_at || b.updated_at) - Date.parse(a.latest_message?.created_at || a.updated_at));
  const timeLabel = (date: string) => new Intl.DateTimeFormat(lang === "th" ? "th-TH" : "en-US", { month: "short", day: "numeric" }).format(new Date(date));

  return (
    <div className="flex flex-col h-full min-h-0 pixel-bg">
      <header className="px-4 md:px-6 page-header pb-3 shrink-0 page-header-bar">
        <h1 className="font-display text-xl font-bold page-title">{copy.title}</h1>
        <p className="text-xs text-muted-foreground mt-2">{inbox.hint}</p>
      </header>
      {error && (
        <button onClick={() => void loadThreads()} className="m-3 p-2 text-xs btn-danger-outline" role="alert">
          {error} · {copy.retry}
        </button>
      )}
      <div className="flex flex-1 min-h-0">
        <aside aria-label={copy.title} className={`${active ? "hidden md:flex" : "flex"} flex-col w-full md:w-80 lg:w-96 shrink-0 border-r border-border bg-background min-h-0`}>
          <div className="p-4 space-y-3 border-b border-border">
            <input type="search" value={search} onChange={event => setSearch(event.target.value)} placeholder={inbox.search} aria-label={inbox.search} className="field-input w-full text-sm" />
            <div className="flex gap-2">
              {(["all", "buying", "selling"] as const).map(value => <button key={value} onClick={() => setFilter(value)} aria-pressed={filter === value} className={`flex-1 rounded-lg px-3 py-2 text-xs font-bold ${filter === value ? "bg-primary text-primary-foreground" : "text-muted-foreground hover:bg-muted"}`}>{inbox[value]}</button>)}
            </div>
          </div>
          <div className="flex-1 overflow-y-auto">
            {loading && (
              <p role="status" className="p-4 text-sm text-muted-foreground">{inbox.loading}</p>
            )}
            {!loading && visibleThreads.length === 0 && (
              <div className="p-8 text-center">
                <p className="font-bold text-sm">{threads.length ? inbox.noMatch : copy.empty}</p>
                <p className="mt-2 text-xs text-muted-foreground">{threads.length ? inbox.search : inbox.start}</p>
              </div>
            )}
            {visibleThreads.map(thread => {
              const person = thread.buyer.id === Number(currentUser?.id) ? thread.seller : thread.buyer;
              return <button key={thread.id} disabled={sending} onClick={() => setActiveId(thread.id)} aria-pressed={active?.id === thread.id}
                className={`flex w-full gap-3 px-4 py-4 text-left border-b border-border transition-colors hover:bg-muted ${active?.id === thread.id ? "bg-primary/10 border-l-2 border-l-primary" : ""}`}>
                <span className="flex items-center justify-center w-11 h-11 shrink-0 rounded-full bg-primary/10 text-primary font-bold overflow-hidden">
                  {person.avatar ? <img src={person.avatar} alt="" className="w-full h-full object-cover" /> : (person.display_name || person.username || "?").slice(0, 2).toUpperCase()}
                </span>
                <span className="min-w-0 flex-1">
                  <span className="flex items-center justify-between gap-2"><span className={`text-sm truncate ${thread.unread_count > 0 ? "font-bold" : "font-medium"}`}>{threadLabel(thread)}</span><time className="text-[10px] text-muted-foreground shrink-0" dateTime={thread.latest_message?.created_at || thread.updated_at}>{timeLabel(thread.latest_message?.created_at || thread.updated_at)}</time></span>
                  <span className="block text-xs text-primary truncate mt-1">{thread.listing.product_name}</span>
                  <span className={`block text-xs truncate mt-1 ${thread.unread_count > 0 ? "font-bold text-foreground" : "text-muted-foreground"}`}>{thread.latest_message ? `${thread.latest_message.author.id === Number(currentUser?.id) ? inbox.you + ": " : ""}${thread.latest_message.body}` : inbox.first}</span>
                </span>
                {thread.unread_count > 0 && (
                  <span aria-label={`${thread.unread_count} ${lang === "th" ? "ข้อความที่ยังไม่ได้อ่าน" : "unread messages"}`}
                    className="self-center shrink-0 min-w-5 h-5 px-1 rounded-full bg-primary text-primary-foreground text-xs font-bold text-center leading-5">
                    {thread.unread_count > 99 ? "99+" : thread.unread_count}
                  </span>
                )}
              </button>;
            })}
          </div>
        </aside>
        {!active && <div className="hidden md:flex flex-1 flex-col items-center justify-center text-center p-8"><div className="text-4xl mb-4">💬</div><h2 className="font-display font-bold">{inbox.select}</h2><p className="text-sm text-muted-foreground mt-2">{inbox.hint}</p></div>}
      {/* Active conversation */}
      {active && (
        <div className="flex flex-col min-h-0 min-w-0 flex-1 md:min-h-0 md:overflow-hidden">
          <div className="px-4 py-3 border-b border-border flex items-center gap-3">
            <button disabled={sending} onClick={() => setActiveId(null)} aria-label={inbox.back} className="md:hidden p-2 text-primary">←</button>
            <span className="rounded-full bg-primary/10 text-primary w-10 h-10 flex items-center justify-center font-bold">{threadLabel(active).slice(0, 2).toUpperCase()}</span>
            <div className="min-w-0"><h2 className="text-sm font-bold truncate">{threadLabel(active)}</h2><p className="text-xs text-muted-foreground">{active.buyer.id === Number(currentUser?.id) ? inbox.buying : inbox.selling}</p></div>
          </div>
          <div className="px-4 py-2 flex justify-between gap-4 shrink-0 chat-toolbar">
            <span className="text-xs font-bold truncate text-foreground">{active.listing.product_name}</span>
            <span className="text-xs font-mono shrink-0 text-primary">
              {formatMoney(Number(active.listing.asking_price), active.listing.currency, lang)}
            </span>
          </div>
          <div className="flex-1 overflow-y-auto p-3 md:p-4 space-y-2 max-w-3xl">
            {threadLoading && <p role="status" className="text-xs text-muted-foreground">{inbox.loading}</p>}
            {messages.map(message => (
              <div key={message.id} className={`flex ${message.author.id === Number(currentUser?.id) ? "justify-end" : "justify-start"}`}>
                <div className={`max-w-[80%] md:max-w-[65%] px-3 py-2 text-sm ${message.author.id === Number(currentUser?.id) ? "chat-bubble-out" : "chat-bubble-in"}`}>
                  <p className="whitespace-pre-wrap break-words">{message.body}</p>
                  <p className="text-[9px] text-muted-foreground mt-1">{message.author.display_name}</p>
                </div>
              </div>
            ))}
            {offers.map(offer => (
              <div key={offer.id} className="p-3 max-w-md offer-card">
                <div className="flex justify-between gap-2">
                  <span className="text-xs text-foreground">{copy.offer}</span>
                  <b className="text-primary">{formatMoney(Number(offer.amount), offer.currency, lang)}</b>
                </div>
                <p className="text-[10px] text-muted-foreground">{offer.proposer.display_name} · {offer.status}</p>
                {offer.status === "pending" && active.seller.id === Number(currentUser?.id) && (
                  <div className="flex gap-2 mt-2">
                    <button onClick={() => void actOnOffer(offer, "accept")} className="btn-primary px-3 py-1 text-xs">{copy.accept}</button>
                    <button onClick={() => void actOnOffer(offer, "decline")} className="px-3 py-1 text-xs btn-danger-outline">{copy.decline}</button>
                  </div>
                )}
              </div>
            ))}
          </div>
          <div className="p-3 md:p-4 space-y-2 shrink-0 max-w-3xl w-full chat-toolbar">
            <div className="flex gap-2">
              <input value={offerAmount} onChange={event => setOfferAmount(event.target.value)} type="number"
                aria-label={`${copy.offer} (${active.listing.currency})`}
                placeholder={`${copy.offer} (${active.listing.currency})`}
                className="flex-1 min-w-0 field-input text-sm" />
              <button onClick={() => void makeOffer()} className="btn-primary px-3 text-xs shrink-0">{copy.offer}</button>
            </div>
            <div className="flex gap-2">
              <input value={body} onChange={event => setBody(event.target.value)}
                onKeyDown={event => event.key === "Enter" && !event.nativeEvent.isComposing && void sendMessage()}
                aria-label={copy.type} placeholder={copy.type}
                className="flex-1 min-w-0 field-input text-sm" />
              <button disabled={sending || !body.trim() || threadLoading} onClick={() => void sendMessage()} className="btn-primary px-3 text-xs shrink-0">{copy.send}</button>
            </div>
            {active.deal && active.deal.status !== "completed" && (
              <button onClick={() => void confirmCompletion()}
                className="w-full py-2 text-xs text-success"
                style={{ border: "1px solid color-mix(in srgb, var(--color-success) 40%, transparent)" }}>
                {copy.complete}
              </button>
            )}
            {active.deal && active.deal.status === "completed" && active.deal.reviewer_has_reviewed !== true && active.deal.counterparty_id && (
              <button
                onClick={() => onLeaveReview({
                  dealId: active.deal!.id,
                  revieweeId: String(active.deal!.counterparty_id),
                  revieweeName: active.deal!.counterparty_name || threadLabel(active),
                })}
                className="w-full py-2 text-xs text-primary"
                style={{ border: "1px solid color-mix(in srgb, var(--color-primary) 40%, transparent)" }}>
                {copy.reviewBanner} {active.deal.counterparty_name || threadLabel(active)} · {copy.leaveReview}
              </button>
            )}
          </div>
        </div>
      )}

      </div>
      {reviewPrompt && (
        <ReviewPromptModal
          lang={lang}
          revieweeName={reviewPrompt.revieweeName}
          onLeaveReview={() => {
            onLeaveReview(reviewPrompt);
            setReviewPrompt(null);
          }}
          onDismiss={() => setReviewPrompt(null)}
        />
      )}
    </div>
  );
}
