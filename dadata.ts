// =============================================================
// DESIGN SYSTEM: "Контрагент" — Dadata API service
// Endpoint: POST https://suggestions.dadata.ru/suggestions/api/4_1/rs/findById/party
// Auth: Authorization: Token <token>
// =============================================================

export interface DadataCompany {
  value: string;
  unrestricted_value: string;
  data: {
    kpp: string | null;
    capital: { type: string; value: number } | null;
    management: { name: string; post: string; start_date: number } | null;
    founders: unknown[] | null;
    managers: unknown[] | null;
    branch_type: string;
    branch_count: number;
    type: string; // LEGAL | INDIVIDUAL
    state: {
      status: string; // ACTIVE | LIQUIDATING | LIQUIDATED | BANKRUPT | REORGANIZING
      actuality_date: number;
      registration_date: number;
      liquidation_date: number | null;
    };
    opf: { full: string; short: string };
    name: {
      full_with_opf: string;
      short_with_opf: string;
      full: string;
      short: string;
    };
    inn: string;
    ogrn: string;
    okpo: string | null;
    okato: string | null;
    oktmo: string | null;
    okved: string;
    okveds: Array<{ main: boolean; code: string; name: string }>;
    authorities: {
      fts_registration?: { name: string; code: string; address: string };
      fts_report?: { name: string; code: string };
    };
    documents: {
      fts_registration?: { type: string; series: string; number: string; issue_date: number };
    };
    licenses: unknown[] | null;
    address: {
      value: string;
      unrestricted_value: string;
      data: {
        postal_code: string;
        region_with_type: string;
        city_with_type: string;
        geo_lat: string;
        geo_lon: string;
      };
    };
    phones: Array<{ value: string }> | null;
    emails: Array<{ value: string }> | null;
    ogrn_date: number;
    okved_type: string;
    employee_count: number | null;
    invalid: string | null;
  };
}

export interface DadataResponse {
  suggestions: DadataCompany[];
}

const DADATA_URL = 'https://suggestions.dadata.ru/suggestions/api/4_1/rs/findById/party';

export async function lookupInn(inn: string, token: string): Promise<DadataCompany | null> {
  const response = await fetch(DADATA_URL, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Accept': 'application/json',
      'Authorization': `Token ${token}`,
    },
    body: JSON.stringify({ query: inn }),
  });

  if (!response.ok) {
    throw new Error(`Ошибка API: ${response.status} ${response.statusText}`);
  }

  const data: DadataResponse = await response.json();
  return data.suggestions[0] ?? null;
}

// ---- Helpers ----

export function formatDate(timestamp: number | null | undefined): string {
  if (!timestamp) return '—';
  return new Date(timestamp).toLocaleDateString('ru-RU', {
    day: '2-digit',
    month: '2-digit',
    year: 'numeric',
  });
}

export function formatCapital(capital: { value: number; type: string } | null): string {
  if (!capital) return '—';
  return new Intl.NumberFormat('ru-RU', {
    style: 'currency',
    currency: 'RUB',
    maximumFractionDigits: 0,
  }).format(capital.value);
}

export function companyAge(registrationDate: number): string {
  const now = new Date();
  const reg = new Date(registrationDate);
  const years = now.getFullYear() - reg.getFullYear();
  const months = now.getMonth() - reg.getMonth();
  const totalMonths = years * 12 + months;
  const y = Math.floor(totalMonths / 12);
  const m = totalMonths % 12;
  if (y === 0) return `${m} мес.`;
  if (m === 0) return `${y} лет`;
  return `${y} лет ${m} мес.`;
}

export type StatusKey = 'ACTIVE' | 'LIQUIDATING' | 'LIQUIDATED' | 'BANKRUPT' | 'REORGANIZING';

export const STATUS_LABELS: Record<StatusKey, string> = {
  ACTIVE: 'Действующее',
  LIQUIDATING: 'Ликвидируется',
  LIQUIDATED: 'Ликвидировано',
  BANKRUPT: 'Банкротство',
  REORGANIZING: 'Реорганизация',
};

export function getStatusClass(status: string): string {
  switch (status) {
    case 'ACTIVE': return 'status-active';
    case 'LIQUIDATING':
    case 'REORGANIZING': return 'status-liquidating';
    case 'LIQUIDATED':
    case 'BANKRUPT': return 'status-liquidated';
    default: return 'status-liquidating';
  }
}

export function validateInn(inn: string): { valid: boolean; type: 'LEGAL' | 'INDIVIDUAL' | null; error?: string } {
  const digits = inn.replace(/\D/g, '');
  if (digits.length === 10) return { valid: true, type: 'LEGAL' };
  if (digits.length === 12) return { valid: true, type: 'INDIVIDUAL' };
  if (digits.length === 0) return { valid: false, type: null };
  return { valid: false, type: null, error: 'ИНН должен содержать 10 цифр (юр. лицо) или 12 цифр (ИП)' };
}
