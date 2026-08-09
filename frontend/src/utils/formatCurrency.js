/**
 * Format a number as currency (USD by default).
 * @param {number|string} amount
 * @param {string} currency
 * @returns {string}
 */
export function formatCurrency(amount, currency = 'INR') {
  const num = parseFloat(amount)
  if (isNaN(num)) return currency === 'INR' ? '₹0' : '$0.00'
  
  if (currency === 'INR') {
    return new Intl.NumberFormat('en-IN', {
      style: 'currency',
      currency: 'INR',
      maximumFractionDigits: 0,
    }).format(num)
  }

  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency,
    minimumFractionDigits: 2,
  }).format(num)
}

export default formatCurrency
