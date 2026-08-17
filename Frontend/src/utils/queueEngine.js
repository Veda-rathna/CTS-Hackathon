/**
 * Prior Authorization Batch Work Queue Engine
 *
 * Deterministic Priority Queue & Sequential Processing Orchestrator
 * Priority controls QUEUE EXECUTION ORDER only (URGENT > MEDIUM > LOW, FIFO within same priority).
 * Policy decision is determined strictly by the existing single-request PA engine.
 */

export const PRIORITY_RANK = {
  URGENT: 3,
  MEDIUM: 2,
  LOW: 1,
};

export const PROCESSING_STATUS = {
  STAGED: 'STAGED',
  QUEUED: 'QUEUED',
  PROCESSING: 'PROCESSING',
  COMPLETED: 'COMPLETED',
  FAILED: 'FAILED',
};

/**
 * Sorts queued requests strictly by priority_rank DESC, then submission_sequence ASC (FIFO).
 * Preserves the active PROCESSING request at the head if present.
 */
export function sortPriorityQueue(requests) {
  if (!Array.isArray(requests)) return [];

  return [...requests].sort((a, b) => {
    // Keep currently processing item at the top
    if (a.processing_status === PROCESSING_STATUS.PROCESSING) return -1;
    if (b.processing_status === PROCESSING_STATUS.PROCESSING) return 1;

    // Completed or Failed items maintain their finished sequence
    const isDoneA = a.processing_status === PROCESSING_STATUS.COMPLETED || a.processing_status === PROCESSING_STATUS.FAILED;
    const isDoneB = b.processing_status === PROCESSING_STATUS.COMPLETED || b.processing_status === PROCESSING_STATUS.FAILED;

    if (isDoneA && !isDoneB) return 1;
    if (!isDoneA && isDoneB) return -1;
    if (isDoneA && isDoneB) {
      return (a.processed_order || 0) - (b.processed_order || 0);
    }

    // Waiting queue: Priority Rank DESC
    const rankA = PRIORITY_RANK[a.priority?.toUpperCase()] || 1;
    const rankB = PRIORITY_RANK[b.priority?.toUpperCase()] || 1;

    if (rankB !== rankA) {
      return rankB - rankA;
    }

    // Same priority: Submission Sequence ASC (FIFO)
    return (a.submission_sequence || 0) - (b.submission_sequence || 0);
  });
}

/**
 * Computes summary statistics from an actual batch of processed items.
 * All metrics derived directly from actual request outcomes.
 */
export function computeBatchSummary(items) {
  if (!Array.isArray(items) || items.length === 0) {
    return {
      total: 0,
      completed: 0,
      failed: 0,
      queued: 0,
      processing: 0,
      decisions: {
        APPROVE: 0,
        PEND: 0,
        NEED_MORE_INFORMATION: 0,
        REJECTED: 0,
      },
      priorities: {
        URGENT: 0,
        MEDIUM: 0,
        LOW: 0,
      },
    };
  }

  const summary = {
    total: items.length,
    completed: items.filter((i) => i.processing_status === PROCESSING_STATUS.COMPLETED).length,
    failed: items.filter((i) => i.processing_status === PROCESSING_STATUS.FAILED).length,
    queued: items.filter((i) => i.processing_status === PROCESSING_STATUS.QUEUED).length,
    processing: items.filter((i) => i.processing_status === PROCESSING_STATUS.PROCESSING).length,
    decisions: {
      APPROVE: 0,
      PEND: 0,
      NEED_MORE_INFORMATION: 0,
      REJECTED: 0,
    },
    priorities: {
      URGENT: 0,
      MEDIUM: 0,
      LOW: 0,
    },
  };

  items.forEach((item) => {
    // Count priorities
    const prio = (item.priority || 'LOW').toUpperCase();
    if (summary.priorities[prio] !== undefined) {
      summary.priorities[prio]++;
    }

    // Count decisions for completed items
    if (item.processing_status === PROCESSING_STATUS.COMPLETED && item.decision) {
      const dec = (item.decision || '').toUpperCase();
      if (dec.includes('APPROV') || dec === 'APPROVE') {
        summary.decisions.APPROVE++;
      } else if (dec === 'REJECTED' || dec === 'EXCLUDED' || dec === 'POLICY_EXCLUSION' || dec === 'NOT_COVERED' || dec === 'DENIED') {
        summary.decisions.REJECTED++;
      } else if (dec === 'PEND' || dec === 'PENDED' || dec === 'PENDING_REVIEW' || dec === 'REVIEW') {
        summary.decisions.PEND++;
      } else {
        summary.decisions.NEED_MORE_INFORMATION++;
      }
    }
  });

  return summary;
}
