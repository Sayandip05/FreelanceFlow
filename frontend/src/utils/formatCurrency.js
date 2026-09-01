/**
 * Format a number as currency (USD $ by default).
 *
 * @param {number|string} amount - The amount to format.
 * @param {string} currency - The ISO currency code (default: 'USD').
 * @returns {string} The formatted currency string.
 */
export function formatCurrency(amount, currency = 'USD') {
  const num = Number(amount)
  if (isNaN(num)) return '$0'

  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
    minimumFractionDigits: 0,
    maximumFractionDigits: 2,
  }).format(num)
}

export default formatCurrency
