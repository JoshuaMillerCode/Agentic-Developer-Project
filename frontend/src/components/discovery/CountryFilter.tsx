"use client";

/**
 * Country/region filter for discovery and chat.
 * Uses TMDb ISO 3166-1 alpha-2 codes.
 */
export const COUNTRY_OPTIONS: { value: string; label: string }[] = [
  { value: "", label: "All regions" },
  { value: "US", label: "United States" },
  { value: "GB", label: "United Kingdom" },
  { value: "CA", label: "Canada" },
  { value: "AU", label: "Australia" },
  { value: "DE", label: "Germany" },
  { value: "FR", label: "France" },
  { value: "IN", label: "India" },
  { value: "JP", label: "Japan" },
  { value: "KR", label: "South Korea" },
  { value: "ES", label: "Spain" },
  { value: "IT", label: "Italy" },
  { value: "BR", label: "Brazil" },
  { value: "MX", label: "Mexico" },
];

export type RegionValue = string;

interface CountryFilterProps {
  value: RegionValue;
  onChange: (region: RegionValue) => void;
  disabled?: boolean;
  className?: string;
}

export function CountryFilter({
  value,
  onChange,
  disabled = false,
  className = "",
}: CountryFilterProps) {
  return (
    <div className={className}>
      <label htmlFor="country-filter" className="sr-only">
        Filter content by country
      </label>
      <select
        id="country-filter"
        value={value}
        onChange={(e) => onChange(e.target.value)}
        disabled={disabled}
        className="rounded-lg bg-surface-800 border border-surface-600 text-gray-200 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-accent-red/50 focus:border-accent-red/30 disabled:opacity-50"
        aria-label="Filter content by country"
      >
        {COUNTRY_OPTIONS.map((opt) => (
          <option key={opt.value || "all"} value={opt.value}>
            {opt.label}
          </option>
        ))}
      </select>
    </div>
  );
}
