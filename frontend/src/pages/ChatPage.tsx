import { useEffect, useState } from "react";
import type { AppLang, User } from "../types";
import { api, type ApiConversation, type ApiMessage, type ApiOffer } from "../lib/api";
import { formatMoney } from "../lib/money";


interface Props {
  lang: AppLang;
  currentUser: User | null;
  isAuthenticated: boolean;
  onSignIn: () => void;
}


export default function ChatPage({ lang, currentUser, isAuthenticated, onSignIn }: Props) {
  const copy = lang === "th" ? {
    title: "ข้อความ", empty: "ยังไม่มีการสนทนา", signIn: "เข้าสู่ระบบเพื่อดูข้อความ",
    type: "พิมพ์ข้อความ...", send: "ส่ง", offer: "เสนอราคา", accept: "ยอมรับ",
    decline: "ปฏิเสธ", complete: "ยืนยันว่าซื้อขายสำเร็จ", retry: "ลองอีกครั้ง",
  } : {
    title: "Messages", empty: "No conversations yet", signIn: "Sign in to view messages",
    type: "Type a message...", send: "Send", offer: "Make offer", accept: "Accept",
    decline: "Decline", complete: "Confirm completed trade", retry: "Try again",
  };
  const [threads, setThreads] = useState<ApiConversation[]>([]);
  const [active, setActive] = useState<ApiConversation | null>(null);
  const [messages, setMessages] = useState<ApiMessage[]>([]);
  const [offers, setOffers] = useState<ApiOffer[]>([]);
  const [body, setBody] = useState("");
  const [offerAmount, setOfferAmount] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const loadThreads = async () => {
    if (!isAuthenticated) return;
    setLoading(true); setError("");
    try {
      const result = await api.conversations();
      setThreads(result);
      setActive(current => current
        ? result.find(thread => thread.id === current.id) ?? result[0] ?? null
        : result[0] ?? null);
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Request failed");
    } finally { setLoading(false); }
  };

  useEffect(() => { void loadThreads(); }, [isAuthenticated]);
  useEffect(() => {
    if (!active) return;
    Promise.all([api.messages(active.id), api.offers(active.id)])
      .then(([nextMessages, nextOffers]) => { setMessages(nextMessages); setOffers(nextOffers); })
      .catch(caught => setError(caught instanceof Error ? caught.message : "Request failed"));
  }, [active?.id]);

  if (!isAuthenticated) return (
    <div className="flex-1 flex flex-col items-center justify-center text-center px-6 pixel-bg">
      <div className="text-5xl mb-4">💬</div><p className="text-muted-foreground mb-4">{copy.signIn}</p>
      <button onClick={onSignIn} className="btn-primary px-6 py-3 text-sm">{copy.signIn}</button>
    </div>
  );

  const sendMessage = async () => {
    if (!active || !body.trim()) return;
    try { const message = await api.sendMessage(active.id, body.trim()); setMessages(items => [...items, message]); setBody(""); }
    catch (caught) { setError(caught instanceof Error ? caught.message : "Request failed"); }
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

  return (
    <div className="flex flex-col md:grid md:grid-cols-[minmax(240px,320px)_1fr] md:grid-rows-[auto_1fr] h-full pixel-bg">
      <header className="md:col-span-2 px-4 md:px-6 page-header pb-3 shrink-0" style={{ borderBottom: "1px solid rgba(255,214,0,.12)" }}>
        <h1 className="font-display text-xl font-bold" style={{ color: "#FFD600" }}>{copy.title}</h1>
      </header>

      {error && (
        <button onClick={() => void loadThreads()} className="md:col-span-2 m-3 p-2 text-xs" style={{ color: "#FF3D57", border: "1px solid #FF3D57" }}>
          {error} · {copy.retry}
        </button>
      )}
      {loading && <p className="md:col-span-2 p-4 text-sm text-muted-foreground">Loading…</p>}
      {!loading && threads.length === 0 && (
        <p className="md:col-span-2 p-8 text-center text-sm text-muted-foreground">{copy.empty}</p>
      )}

      {/* Thread list — horizontal scroll on mobile, sidebar on desktop */}
      {threads.length > 0 && (
        <div className="md:row-span-1 md:overflow-y-auto md:border-r shrink-0"
          style={{ borderColor: "rgba(255,255,255,.08)" }}>
          <div className="flex md:flex-col gap-2 overflow-x-auto md:overflow-x-visible px-3 md:px-2 py-3 md:py-2 scroll-hide">
            {threads.map(thread => (
              <button key={thread.id} onClick={() => setActive(thread)}
                className="shrink-0 md:shrink md:w-full px-3 py-2 md:py-3 text-left transition-colors"
                style={{
                  border: `1px solid ${active?.id === thread.id ? "#FFD600" : "rgba(255,255,255,.1)"}`,
                  borderRadius: 4,
                  background: active?.id === thread.id ? "rgba(255,214,0,.06)" : "transparent",
                }}>
                <p className="text-xs font-bold text-foreground truncate">{thread.listing.product_name}</p>
                <p className="text-[10px] text-muted-foreground truncate">{threadLabel(thread)}</p>
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Active conversation */}
      {active && (
        <div className="flex flex-col min-h-0 flex-1 md:min-h-0 md:overflow-hidden">
          <div className="px-4 py-2 flex justify-between gap-4 shrink-0" style={{ background: "rgba(255,214,0,.05)" }}>
            <span className="text-xs font-bold truncate">{active.listing.product_name}</span>
            <span className="text-xs font-mono shrink-0" style={{ color: "#FFD600" }}>
              {formatMoney(Number(active.listing.asking_price), active.listing.currency, lang)}
            </span>
          </div>
          <div className="flex-1 overflow-y-auto p-3 md:p-4 space-y-2 max-w-3xl">
            {messages.map(message => (
              <div key={message.id} className={`flex ${message.author.id === Number(currentUser?.id) ? "justify-end" : "justify-start"}`}>
                <div className="max-w-[80%] md:max-w-[65%] px-3 py-2 text-sm"
                  style={{ background: message.author.id === Number(currentUser?.id) ? "rgba(255,214,0,.15)" : "#0C0E28", borderRadius: 6 }}>
                  <p>{message.body}</p>
                  <p className="text-[9px] text-muted-foreground mt-1">{message.author.display_name}</p>
                </div>
              </div>
            ))}
            {offers.map(offer => (
              <div key={offer.id} className="p-3 max-w-md" style={{ border: "1px solid rgba(255,214,0,.25)", borderRadius: 5 }}>
                <div className="flex justify-between gap-2">
                  <span className="text-xs">{copy.offer}</span>
                  <b style={{ color: "#FFD600" }}>{formatMoney(Number(offer.amount), offer.currency, lang)}</b>
                </div>
                <p className="text-[10px] text-muted-foreground">{offer.proposer.display_name} · {offer.status}</p>
                {offer.status === "pending" && active.seller.id === Number(currentUser?.id) && (
                  <div className="flex gap-2 mt-2">
                    <button onClick={() => void actOnOffer(offer, "accept")} className="btn-primary px-3 py-1 text-xs">{copy.accept}</button>
                    <button onClick={() => void actOnOffer(offer, "decline")} className="px-3 py-1 text-xs" style={{ color: "#FF3D57", border: "1px solid #FF3D57" }}>{copy.decline}</button>
                  </div>
                )}
              </div>
            ))}
          </div>
          <div className="p-3 md:p-4 space-y-2 shrink-0 max-w-3xl w-full" style={{ borderTop: "1px solid rgba(255,255,255,.08)" }}>
            <div className="flex gap-2">
              <input value={offerAmount} onChange={event => setOfferAmount(event.target.value)} type="number"
                aria-label={`${copy.offer} (${active.listing.currency})`}
                placeholder={`${copy.offer} (${active.listing.currency})`}
                className="flex-1 min-w-0 px-3 py-2 text-sm" style={{ background: "#0C0E28", border: "1px solid rgba(255,255,255,.1)" }} />
              <button onClick={() => void makeOffer()} className="btn-primary px-3 text-xs shrink-0">{copy.offer}</button>
            </div>
            <div className="flex gap-2">
              <input value={body} onChange={event => setBody(event.target.value)}
                onKeyDown={event => event.key === "Enter" && void sendMessage()}
                aria-label={copy.type} placeholder={copy.type}
                className="flex-1 min-w-0 px-3 py-2 text-sm" style={{ background: "#0C0E28", border: "1px solid rgba(255,255,255,.1)" }} />
              <button onClick={() => void sendMessage()} className="btn-primary px-3 text-xs shrink-0">{copy.send}</button>
            </div>
            {active.deal && active.deal.status !== "completed" && (
              <button onClick={async () => { await api.confirmDeal(active.deal!.id); await loadThreads(); }}
                className="w-full py-2 text-xs" style={{ border: "1px solid rgba(0,230,118,.4)", color: "#00E676" }}>
                {copy.complete}
              </button>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
