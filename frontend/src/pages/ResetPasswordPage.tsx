import { useState } from 'react';
import type { AppLang } from '../types';
import { i18n } from '../i18n';
import { api } from '../lib/api';
import type { ResetLink } from '../lib/resetLink';

interface Props {
  lang: AppLang;
  link: ResetLink;
  onDone: () => void;
}

export default function ResetPasswordPage({ lang, link, onDone }: Props) {
  const t = i18n[lang];
  const [password, setPassword] = useState('');
  const [confirmation, setConfirmation] = useState('');
  const [error, setError] = useState('');
  const [saving, setSaving] = useState(false);
  const [done, setDone] = useState(false);
  const mismatch = confirmation.length > 0 && confirmation !== password;
  const canSave = password.length >= 8 && password === confirmation && !saving;
  const inputClass = 'field-input font-body text-sm mb-3 block';

  const save = async () => {
    setSaving(true);
    setError('');
    try {
      await api.confirmPasswordReset(link.uid, link.token, password);
      setDone(true);
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : 'Request failed');
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="flex flex-col min-h-full overflow-y-auto bg-background">
      <div className="px-5 pt-14 pb-8 max-w-md w-full mx-auto animate-slide-up">
        <p className="font-pixel text-[10px] mb-3 text-accent text-center" style={{ letterSpacing: '0.15em' }}>POKEFIND</p>
        <h1 className="font-display text-2xl font-bold text-foreground text-center mb-6">{t.resetPasswordTitle}</h1>
        {done ? (
          <>
            <p className="text-sm text-center text-success mb-6">✓ {t.passwordUpdated}</p>
            <button onClick={onDone} className="w-full py-3 text-sm font-bold btn-primary" style={{ borderRadius: 4 }}>
              {t.backToSignIn} →
            </button>
          </>
        ) : (
          <>
            <input type="password" value={password} onChange={e => setPassword(e.target.value)}
              aria-label={t.newPassword} autoComplete="new-password" placeholder={t.newPassword} className={inputClass} />
            <input type="password" value={confirmation} onChange={e => setConfirmation(e.target.value)}
              aria-label={t.confirmNewPassword} autoComplete="new-password" placeholder={t.confirmNewPassword}
              className={inputClass} />
            {mismatch && <p className="text-xs mb-3 text-danger">{t.passwordsDontMatch}</p>}
            {error && <p className="text-xs mb-3 text-danger">{error}</p>}
            <button disabled={!canSave} onClick={() => void save()}
              className="w-full py-3 text-sm font-bold btn-primary" style={{ borderRadius: 4, opacity: canSave ? 1 : 0.45 }}>
              {saving ? t.loading : t.saveNewPassword}
            </button>
            <button onClick={onDone} className="w-full py-2.5 mt-2 text-sm text-muted-foreground">{t.backToSignIn}</button>
          </>
        )}
      </div>
    </div>
  );
}
