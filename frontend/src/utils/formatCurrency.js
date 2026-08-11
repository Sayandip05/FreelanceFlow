/**
 * Format a number as currency (USD $ by default).
 * @param {number|string} amount
 * @param {string} currency
 * @returns {string}
 */
export function formatCurrency(amount, currency = 'USD') {
  const num = parseFloat(amount)
  if (isNaN(num)) return '$0.00'

  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
    minimumFractionDigits: 0,
    maximumFractionDigits: 2,
  }).format(num)
}

export default formatCurrency
