# Dadata findById/party API

## Endpoint

```
POST https://suggestions.dadata.ru/suggestions/api/4_1/rs/findById/party
```

## Headers

```
Content-Type: application/json
Accept: application/json
Authorization: Token <DADATA_TOKEN>
```

## Request body

```json
{ "query": "7707083893" }
```

`query` — ИНН (10 цифр юр. лицо, 12 цифр ИП) или ОГРН.

## CORS

Dadata allows `Access-Control-Allow-Origin: *`, so direct browser requests work without a proxy.

## Response structure

```json
{
  "suggestions": [
    {
      "value": "ПАО СБЕРБАНК",
      "unrestricted_value": "ПАО СБЕРБАНК",
      "data": { ... }
    }
  ]
}
```

Empty `suggestions` array = not found.

## Key `data` fields

| Field | Type | Description |
|-------|------|-------------|
| `inn` | string | ИНН |
| `kpp` | string\|null | КПП |
| `ogrn` | string | ОГРН |
| `okpo` | string | ОКПО |
| `okato` | string | ОКАТО |
| `oktmo` | string | ОКТМО |
| `okved` | string | Основной ОКВЭД код |
| `type` | string | `LEGAL` \| `INDIVIDUAL` |
| `name.short_with_opf` | string | Краткое наименование с ОПФ |
| `name.full_with_opf` | string | Полное наименование с ОПФ |
| `state.status` | string | `ACTIVE` \| `LIQUIDATING` \| `LIQUIDATED` \| `BANKRUPT` \| `REORGANIZING` |
| `state.registration_date` | number | Timestamp регистрации (ms) |
| `state.liquidation_date` | number\|null | Timestamp ликвидации |
| `management.name` | string | ФИО руководителя |
| `management.post` | string | Должность |
| `capital.value` | number | Уставный капитал |
| `capital.type` | string | Тип капитала |
| `address.value` | string | Адрес кратко |
| `address.unrestricted_value` | string | Адрес полный |
| `address.data.postal_code` | string | Индекс |
| `address.data.region_with_type` | string | Регион |
| `okveds[]` | array | Все ОКВЭД: `{ main, code, name }` |
| `authorities.fts_registration` | object | Налоговый орган: `{ name, code, address }` |
| `authorities.fts_report` | object | Отчётный орган: `{ name, code }` |
| `phones[]` | array\|null | Телефоны: `{ value }` |
| `emails[]` | array\|null | Email: `{ value }` |
| `branch_count` | number | Число филиалов |
| `ogrn_date` | number | Timestamp даты ОГРН |
| `employee_count` | number\|null | Число сотрудников |

## TypeScript interface

```typescript
export interface DadataCompany {
  value: string;
  unrestricted_value: string;
  data: {
    kpp: string | null;
    capital: { type: string; value: number } | null;
    management: { name: string; post: string; start_date: number } | null;
    founders: any[] | null;
    managers: any[] | null;
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
    okpo: string;
    okato: string;
    oktmo: string;
    okved: string;
    okveds: Array<{ main: boolean; code: string; name: string }>;
    authorities: {
      fts_registration?: { name: string; code: string; address: string };
      fts_report?: { name: string; code: string };
    };
    documents: {
      fts_registration?: { type: string; series: string; number: string; issue_date: number };
    };
    licenses: any[] | null;
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
```

## Status mapping (Russian)

| API status | Russian | Color |
|------------|---------|-------|
| ACTIVE | Действующее | green/success |
| LIQUIDATING | Ликвидируется | yellow/warning |
| LIQUIDATED | Ликвидировано | red/destructive |
| BANKRUPT | Банкротство | red/destructive |
| REORGANIZING | Реорганизация | yellow/warning |

## Org type mapping

| API type | Russian |
|----------|---------|
| LEGAL | Юридическое лицо |
| INDIVIDUAL | Индивидуальный предприниматель |
