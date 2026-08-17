/**
 * Helper formatters for Prior Authorization dates, codes, and text.
 */

export function formatDate(dateString) {
  if (!dateString) return 'N/A';
  try {
    const d = new Date(dateString);
    if (isNaN(d.getTime())) return dateString;
    return d.toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
    });
  } catch {
    return dateString;
  }
}

export function formatDateTime(isoString) {
  if (!isoString) return 'N/A';
  try {
    const d = new Date(isoString);
    if (isNaN(d.getTime())) return isoString;
    return d.toLocaleString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  } catch {
    return isoString;
  }
}

export function formatStatusLabel(status) {
  if (!status) return 'Unknown';
  switch (status.toUpperCase()) {
    case 'APPROVE':
    case 'APPROVED':
      return 'Approved';
    case 'PEND':
    case 'PENDED':
    case 'PENDING':
    case 'PENDING_REVIEW':
    case 'DENY':
    case 'DENIED':
    case 'POLICY_EXPIRED':
      return 'Pended for Review';
    case 'NEED_MORE_INFORMATION':
    case 'REQUEST_MORE_INFORMATION':
    case 'ADDITIONAL_EVIDENCE_REQUIRED':
      return 'Need More Information';
    default:
      return status.replace(/_/g, ' ');
  }
}

export function truncateText(text, maxLength = 60) {
  if (!text) return '';
  if (text.length <= maxLength) return text;
  return text.substring(0, maxLength) + '...';
}

export function formatScorePercent(score) {
  if (score === null || score === undefined) return 'N/A';
  return `${Math.round(score * 100)}%`;
}
