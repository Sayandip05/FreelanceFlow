/**
 * Format a number as currency (INR ₹ by default).
 *
 * @param {number|string} amount - The amount to format.
 * @param {string} currency - The ISO currency code (default: 'INR').
 * @returns {string} The formatted currency string.
 */
export function formatCurrency(amount, currency = 'INR') {
  const num = Number(amount)
  if (isNaN(num)) return '₹0'

  return new Intl.NumberFormat('en-IN', {
    style: 'currency',
    currency: currency,
    minimumFractionDigits: 0,
    maximumFractionDigits: 2,
  }).format(num)
}

export default formatCurrency
