import React, { useState, useEffect, useRef } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import {
  Layers,
  Play,
  Pause,
  PlusCircle,
  RefreshCw,
  Eye,
  CheckCircle2,
  AlertCircle,
  Clock,
  RotateCcw,
  ArrowRight,
  ShieldCheck,
  Zap,
} from 'lucide-react';
import { runTriage } from '../services/api';
import { savePARequest } from '../utils/storage';
import {
  sortPriorityQueue,
  computeBatchSummary,
  PROCESSING_STATUS,
  PRIORITY_RANK,
} from '../utils/queueEngine';
import PriorityBadge from '../components/common/PriorityBadge';
import DecisionBadge from '../components/common/DecisionBadge';
import EmptyState from '../components/common/EmptyState';
import CurrentlyProcessingCard from '../components/queue/CurrentlyProcessingCard';
import BatchSummaryCard from '../components/queue/BatchSummaryCard';
import BatchIntakeModal from '../components/queue/BatchIntakeModal';

const BATCH_QUEUE_STORAGE_KEY = 'pa_batch_work_queue_state_v1';

export default function BatchQueue() {
  const navigate = useNavigate();
  const [queue, setQueue] = useState([]);
  const [batchId, setBatchId] = useState(`BATCH-${Date.now().toString().slice(-6)}`);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [isAutoRunning, setIsAutoRunning] = useState(false);

  // Concurrency lock to prevent duplicate runs
  const isRunningRef = useRef(false);
  const queueRef = useRef(queue);
  queueRef.current = queue;

  // Load saved queue on mount if available
  useEffect(() => {
    try {
      const saved = sessionStorage.getItem(BATCH_QUEUE_STORAGE_KEY);
      if (saved) {
        const parsed = JSON.parse(saved);
        if (Array.isArray(parsed.items) && parsed.items.length > 0) {
          setQueue(parsed.items);
          if (parsed.batchId) setBatchId(parsed.batchId);
        }
      }
    } catch (e) {
      console.warn('Could not restore queue session:', e);
    }
  }, []);

  // Save queue session on state change
  useEffect(() => {
    try {
      sessionStorage.setItem(
        BATCH_QUEUE_STORAGE_KEY,
        JSON.stringify({ batchId, items: queue })
      );
    } catch (e) {
      console.warn('Could not persist queue session:', e);
    }
  }, [queue, batchId]);

  // Sequential Queue Processing Engine
  const processNextInQueue = async () => {
    if (isRunningRef.current) return;

    const currentItems = queueRef.current;
    // Find next QUEUED item sorted by deterministic priority
    const waitingItems = currentItems.filter((i) => i.processing_status === PROCESSING_STATUS.QUEUED);
    if (waitingItems.length === 0) {
      setIsAutoRunning(false);
      return;
    }

    // Sort waiting items by priority_rank DESC, submission_sequence ASC
    const sortedWaiting = sortPriorityQueue(waitingItems);
    const targetItem = sortedWaiting[0];
    if (!targetItem) {
      setIsAutoRunning(false);
      return;
    }

    isRunningRef.current = true;
    setIsAutoRunning(true);

    // 1. Mark target item as PROCESSING
    setQueue((prev) =>
      prev.map((item) =>
        item.pa_request_id === targetItem.pa_request_id
          ? { ...item, processing_status: PROCESSING_STATUS.PROCESSING, started_at: new Date().toISOString() }
          : item
      )
    );

    try {
      // 2. Prepare payload for existing single-request PA engine (POST /api/v1/triage)
      const payload = {
        procedure_code: targetItem.procedure_code.trim().toUpperCase(),
        diagnosis_codes: (targetItem.diagnosis_codes || []).map((c) => c.trim().toUpperCase()).filter(Boolean),
        state: targetItem.state || 'TX',
        patient_age: targetItem.patient_age ? Number(targetItem.patient_age) : null,
        clinical_notes: targetItem.clinical_notes || null,
        service_date: targetItem.service_date || new Date().toISOString().split('T')[0],
      };

      // Call existing backend PA Engine
      const triageResponse = await runTriage(payload);

      // 3. Save to existing application storage (individual result retained)
      const savedRecord = savePARequest(
        {
          pa_request_id: targetItem.pa_request_id,
          priority: targetItem.priority,
          source_document: targetItem.source_document || 'Batch Work Queue Intake',
          procedure_code: payload.procedure_code,
          diagnosis_codes: payload.diagnosis_codes,
          state: payload.state,
          patient_age: payload.patient_age,
          clinical_notes: payload.clinical_notes,
          created_at: new Date().toISOString(),
        },
        triageResponse
      );

      // 4. Mark item as COMPLETED with authorization decision
      setQueue((prev) => {
        const completedCount = prev.filter((i) => i.processing_status === PROCESSING_STATUS.COMPLETED).length;
        return prev.map((item) =>
          item.pa_request_id === targetItem.pa_request_id
            ? {
                ...item,
                processing_status: PROCESSING_STATUS.COMPLETED,
                decision: triageResponse.decision || 'PENDING_REVIEW',
                evidence_score: triageResponse.evidence_score,
                processed_order: completedCount + 1,
                completed_at: new Date().toISOString(),
              }
            : item
        );
      });
    } catch (err) {
      console.error(`Batch processing failure on ${targetItem.pa_request_id}:`, err);
      // 5. Error Isolation: Mark FAILED without aborting the rest of the batch
      setQueue((prev) =>
        prev.map((item) =>
          item.pa_request_id === targetItem.pa_request_id
            ? {
                ...item,
                processing_status: PROCESSING_STATUS.FAILED,
                error_message: err.message || 'Evaluation service error',
                completed_at: new Date().toISOString(),
              }
            : item
        )
      );
    } finally {
      isRunningRef.current = false;
    }
  };

  // Continue sequential processing loop
  useEffect(() => {
    if (isAutoRunning && !isRunningRef.current) {
      const hasQueued = queue.some((i) => i.processing_status === PROCESSING_STATUS.QUEUED);
      if (hasQueued) {
        const timer = setTimeout(() => {
          processNextInQueue();
        }, 500);
        return () => clearTimeout(timer);
      } else {
        setIsAutoRunning(false);
      }
    }
  }, [queue, isAutoRunning]);

  // Handle batch intake enqueue
  const handleEnqueueBatch = (newRequests, autoStart = true) => {
    setQueue((prev) => {
      const startSequence = prev.length;
      const formattedNew = newRequests.map((r, i) => ({
        ...r,
        submission_sequence: startSequence + i + 1,
        processing_status: PROCESSING_STATUS.QUEUED,
        decision: null,
      }));
      return [...prev, ...formattedNew];
    });

    if (autoStart) {
      setIsAutoRunning(true);
    }
  };

  // Queue controls
  const handleStartQueue = () => {
    if (isAutoRunning || isRunningRef.current) return;
    setIsAutoRunning(true);
    processNextInQueue();
  };

  const handlePauseQueue = () => {
    setIsAutoRunning(false);
  };

  const handleClearCompleted = () => {
    setQueue((prev) => prev.filter((i) => i.processing_status !== PROCESSING_STATUS.COMPLETED && i.processing_status !== PROCESSING_STATUS.FAILED));
  };

  const handleResetQueue = () => {
    setIsAutoRunning(false);
    isRunningRef.current = false;
    setQueue([]);
    setBatchId(`BATCH-${Date.now().toString().slice(-6)}`);
    sessionStorage.removeItem(BATCH_QUEUE_STORAGE_KEY);
  };

  // Derived metrics
  const summary = computeBatchSummary(queue);
  const activeItem = queue.find((i) => i.processing_status === PROCESSING_STATUS.PROCESSING);
  const displayQueue = sortPriorityQueue(queue);

  return (
    <div className="space-y-5">
      {/* Executive Batch Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-3 border-b border-slate-200/90">
        <div>
          <div className="flex items-center gap-2">
            <h2 className="text-xl sm:text-2xl font-extrabold text-slate-900 tracking-tight">
              Prior Authorization Work Queue
            </h2>
            <span className="text-[10px] font-bold font-mono uppercase tracking-wider text-sky-800 bg-sky-50 px-2 py-0.5 rounded border border-sky-200">
              {batchId}
            </span>
          </div>
          <p className="text-xs sm:text-sm text-slate-500 mt-0.5">
            Deterministic priority queue orchestration (URGENT &rarr; MEDIUM &rarr; LOW, FIFO) with single-request sequential evaluation
          </p>
        </div>

        <div className="flex flex-wrap items-center gap-2 self-start sm:self-auto">
          <button
            type="button"
            onClick={() => setIsModalOpen(true)}
            className="inline-flex items-center gap-1.5 px-4 py-2 text-xs font-bold text-white bg-sky-700 hover:bg-sky-800 rounded-lg shadow-sm transition-colors"
          >
            <PlusCircle className="w-3.5 h-3.5" />
            <span>Stage New Batch</span>
          </button>
        </div>
      </div>

      {/* Queue Status Counters Bar */}
      <div className="grid grid-cols-2 sm:grid-cols-5 gap-3 text-xs">
        <div className="p-3 rounded-xl bg-white border border-slate-200 shadow-2xs">
          <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider block">
            Total Batch
          </span>
          <span className="text-lg font-extrabold text-slate-900">{summary.total}</span>
        </div>

        <div className="p-3 rounded-xl bg-white border border-emerald-200 shadow-2xs">
          <span className="text-[10px] font-bold text-emerald-800 uppercase tracking-wider block">
            Completed
          </span>
          <span className="text-lg font-extrabold text-emerald-800">{summary.completed}</span>
        </div>

        <div className="p-3 rounded-xl bg-white border border-sky-200 shadow-2xs">
          <span className="text-[10px] font-bold text-sky-800 uppercase tracking-wider block">
            Currently Processing
          </span>
          <span className="text-lg font-extrabold text-sky-800">{summary.processing}</span>
        </div>

        <div className="p-3 rounded-xl bg-white border border-slate-200 shadow-2xs">
          <span className="text-[10px] font-bold text-slate-500 uppercase tracking-wider block">
            Waiting in Queue
          </span>
          <span className="text-lg font-extrabold text-slate-700">{summary.queued}</span>
        </div>

        <div className="p-3 rounded-xl bg-white border border-rose-200 shadow-2xs col-span-2 sm:col-span-1">
          <span className="text-[10px] font-bold text-rose-800 uppercase tracking-wider block">
            Failed
          </span>
          <span className="text-lg font-extrabold text-rose-800">{summary.failed}</span>
        </div>
      </div>

      {/* Currently Processing Card */}
      {activeItem && <CurrentlyProcessingCard activeItem={activeItem} />}

      {/* Batch Summary (shown when batch has completed items) */}
      <BatchSummaryCard items={queue} />

      {/* Main Work Queue Table Card */}
      <div className="healthcare-card overflow-hidden bg-white shadow-sm">
        {/* Table Toolbar & Actions */}
        <div className="p-3.5 sm:p-4 border-b border-slate-200/90 bg-white flex flex-col sm:flex-row sm:items-center justify-between gap-3">
          <div className="flex items-center gap-2">
            <h3 className="text-xs font-bold text-slate-800 uppercase tracking-wider">
              Priority Execution Queue ({displayQueue.length} Requests)
            </h3>
            {isAutoRunning && (
              <span className="inline-flex items-center gap-1 text-[10px] font-bold text-sky-800 bg-sky-50 px-2 py-0.5 rounded border border-sky-200">
                <span className="w-1.5 h-1.5 rounded-full bg-sky-600 animate-pulse" />
                Sequential Runner Active
              </span>
            )}
          </div>

          <div className="flex flex-wrap items-center gap-2">
            {summary.queued > 0 && !isAutoRunning && (
              <button
                type="button"
                onClick={handleStartQueue}
                className="inline-flex items-center gap-1.5 px-3.5 py-1.5 text-xs font-bold text-white bg-emerald-700 hover:bg-emerald-800 rounded-lg shadow-sm transition-colors"
              >
                <Play className="w-3.5 h-3.5" />
                <span>Start Batch Evaluation</span>
              </button>
            )}

            {isAutoRunning && (
              <button
                type="button"
                onClick={handlePauseQueue}
                className="inline-flex items-center gap-1.5 px-3.5 py-1.5 text-xs font-bold text-amber-800 bg-amber-50 hover:bg-amber-100 border border-amber-300 rounded-lg transition-colors"
              >
                <Pause className="w-3.5 h-3.5" />
                <span>Pause Queue</span>
              </button>
            )}

            {summary.completed > 0 && (
              <button
                type="button"
                onClick={handleClearCompleted}
                className="px-2.5 py-1.5 text-xs font-bold text-slate-600 hover:text-slate-800 bg-white hover:bg-slate-50 border border-slate-200 rounded-lg transition-colors"
              >
                Clear Completed
              </button>
            )}

            {queue.length > 0 && (
              <button
                type="button"
                onClick={handleResetQueue}
                className="p-1.5 text-xs text-slate-400 hover:text-rose-600 rounded-lg hover:bg-rose-50 transition-colors"
                title="Reset work queue"
              >
                <RotateCcw className="w-3.5 h-3.5" />
              </button>
            )}
          </div>
        </div>

        {/* Priority Order Explanation Banner */}
        <div className="px-4 py-2 bg-slate-50 border-b border-slate-200/80 flex flex-wrap items-center justify-between gap-2 text-[11px] text-slate-600">
          <span>
            <strong>Queue Order Rule:</strong> Requests are ordered by workflow priority (<strong className="text-slate-900">URGENT &gt; MEDIUM &gt; LOW</strong>). Same priority requests are evaluated in submission order (FIFO).
          </span>
          <span className="font-mono text-[10px] text-slate-400 hidden sm:inline">
            Non-interruption rule: Active requests complete uninterrupted
          </span>
        </div>

        {/* Queue Table */}
        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse">
            <thead>
              <tr>
                <th className="table-header w-12 text-center">Pos</th>
                <th className="table-header">PA Request ID</th>
                <th className="table-header">Priority</th>
                <th className="table-header">Procedure Code</th>
                <th className="table-header">Primary Indication</th>
                <th className="table-header">State</th>
                <th className="table-header">Processing Status</th>
                <th className="table-header">Authorization Decision</th>
                <th className="table-header text-right">Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 bg-white">
              {displayQueue.length === 0 ? (
                <tr>
                  <td colSpan="9" className="p-8">
                    <EmptyState
                      icon={Layers}
                      title="Prior Authorization Work Queue is Empty"
                      description="Stage a batch of multiple PA requests using manual entry, PDF document packets, or the demo staging preset to begin prioritized evaluation."
                      actionLabel="Stage New Batch"
                      onAction={() => setIsModalOpen(true)}
                    />
                  </td>
                </tr>
              ) : (
                displayQueue.map((item, idx) => {
                  const isProcessing = item.processing_status === PROCESSING_STATUS.PROCESSING;
                  const isCompleted = item.processing_status === PROCESSING_STATUS.COMPLETED;
                  const isFailed = item.processing_status === PROCESSING_STATUS.FAILED;

                  return (
                    <tr
                      key={item.pa_request_id || idx}
                      className={`transition-colors ${
                        isProcessing
                          ? 'bg-sky-50/50 font-medium'
                          : isCompleted
                          ? 'hover:bg-slate-50/70'
                          : isFailed
                          ? 'bg-rose-50/30'
                          : 'hover:bg-slate-50/50 text-slate-700'
                      }`}
                    >
                      {/* Position / Sequence */}
                      <td className="table-cell text-center font-mono font-bold text-xs">
                        {isProcessing ? (
                          <RefreshCw className="w-3.5 h-3.5 text-sky-600 animate-spin mx-auto" />
                        ) : (
                          <span className="text-slate-400">#{idx + 1}</span>
                        )}
                      </td>

                      {/* PA Request ID */}
                      <td className="table-cell font-mono font-bold text-sky-800">
                        {isCompleted ? (
                          <Link to={`/pa/${item.pa_request_id}`} className="hover:underline">
                            {item.pa_request_id}
                          </Link>
                        ) : (
                          <span>{item.pa_request_id}</span>
                        )}
                      </td>

                      {/* Priority */}
                      <td className="table-cell">
                        <PriorityBadge priority={item.priority} size="xs" />
                      </td>

                      {/* Procedure */}
                      <td className="table-cell font-mono font-bold text-xs">
                        <span className="px-1.5 py-0.5 rounded bg-sky-50 text-sky-800 border border-sky-200">
                          {item.procedure_code || '64483'}
                        </span>
                      </td>

                      {/* Diagnosis Codes */}
                      <td className="table-cell">
                        <div className="flex flex-wrap gap-1">
                          {(item.diagnosis_codes || []).map((d, i) => (
                            <span
                              key={i}
                              className="px-1.5 py-0.2 text-[11px] font-mono font-bold bg-slate-100 text-slate-700 border border-slate-200 rounded"
                            >
                              {d}
                            </span>
                          ))}
                        </div>
                      </td>

                      {/* State */}
                      <td className="table-cell text-xs font-semibold text-slate-700">
                        {item.state || 'TX'}
                      </td>

                      {/* Processing Status */}
                      <td className="table-cell">
                        <span
                          className={`px-2 py-0.5 rounded text-[10px] font-bold border ${
                            isProcessing
                              ? 'bg-sky-100 text-sky-900 border-sky-300 animate-pulse'
                              : isCompleted
                              ? 'bg-emerald-50 text-emerald-800 border-emerald-200'
                              : isFailed
                              ? 'bg-rose-50 text-rose-800 border-rose-200'
                              : 'bg-slate-100 text-slate-600 border-slate-200'
                          }`}
                        >
                          {item.processing_status}
                        </span>
                      </td>

                      {/* Authorization Decision */}
                      <td className="table-cell">
                        {isCompleted && item.decision ? (
                          <DecisionBadge decision={item.decision} size="xs" />
                        ) : isFailed ? (
                          <span className="text-[11px] text-rose-700 font-semibold" title={item.error_message}>
                            Failed (API error)
                          </span>
                        ) : (
                          <span className="text-slate-400 text-xs italic">—</span>
                        )}
                      </td>

                      {/* Action */}
                      <td className="table-cell text-right">
                        {isCompleted ? (
                          <Link
                            to={`/pa/${item.pa_request_id}`}
                            className="inline-flex items-center gap-1 px-2.5 py-1 text-xs font-bold text-sky-800 bg-sky-50 hover:bg-sky-100 border border-sky-200 rounded-lg transition-colors"
                          >
                            <Eye className="w-3 h-3" />
                            <span>Details</span>
                          </Link>
                        ) : (
                          <span className="text-[11px] text-slate-400">Waiting</span>
                        )}
                      </td>
                    </tr>
                  );
                })
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Batch Intake Modal */}
      <BatchIntakeModal
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        onEnqueueBatch={handleEnqueueBatch}
      />
    </div>
  );
}
