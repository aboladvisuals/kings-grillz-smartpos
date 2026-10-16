import { useRef, useState } from "react";
import { apiGet, apiSend } from "./lib/api";
import type { OrderDetails } from "./lib/api";
import { allowedStatuses, statusAction } from "./lib/orderStatus";
import type { OrderStatus, OrderStatusResponse } from "./lib/orderStatus";

type Props = {
  orderId: number;
  details: OrderDetails;
  onStatusChanged: (id: number, status: string) => void;
};

export default function OrderStatusPanel({ orderId, details, onStatusChanged }: Props) {
  const inFlight = useRef(false);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");
  const [needsRefresh, setNeedsRefresh] = useState(false);
  const [confirmCancel, setConfirmCancel] = useState(false);
  const options = allowedStatuses(details.order_status, details.fulfilment);

  async function refreshStatus() {
    const latest = await apiGet<OrderDetails>(`/api/orders/${orderId}`);
    onStatusChanged(orderId, latest.order_status);
    setNeedsRefresh(false);
  }

  async function retryRefresh() {
    if (inFlight.current) return;
    inFlight.current = true;
    setSaving(true);
    try {
      await refreshStatus();
      setError("");
    } catch {
      setError("Could not refresh this order. Check your connection and try again.");
    } finally {
      inFlight.current = false;
      setSaving(false);
    }
  }

  async function updateStatus(next: OrderStatus) {
    if (inFlight.current || needsRefresh || !options.includes(next)) return;
    if (next === "cancelled" && !confirmCancel) {
      setConfirmCancel(true);
      return;
    }
    setConfirmCancel(false);
    inFlight.current = true;
    setSaving(true);
    setError("");
    setSuccess("");
    try {
      const result = await apiSend<OrderStatusResponse>(
        `/api/orders/${orderId}/status`, "PATCH", { order_status: next },
      );
      onStatusChanged(orderId, result.order_status);
      setSuccess(`Order status updated to ${result.order_status}.`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not update order status.");
      // A rejected transition or lost response may mean our view is stale.
      setNeedsRefresh(true);
      try { await refreshStatus(); } catch {
        setError(previous => `${previous} Refresh the order status before trying again.`);
      }
    } finally {
      inFlight.current = false;
      setSaving(false);
    }
  }

  return (
    <section className="fulfilment-panel" aria-label="Order fulfilment" aria-busy={saving}>
      <h3>Order fulfilment</h3>
      <p>{details.fulfilment} · <strong>{details.order_status}</strong></p>
      <div className="fulfilment-actions">
        {options.map(next => (
          <button key={next} type="button" className={next === "cancelled" ? "cancel-order" : ""}
            disabled={saving || needsRefresh || confirmCancel} onClick={() => void updateStatus(next)}>
            {statusAction(next, details.fulfilment)}
          </button>
        ))}
      </div>
      {confirmCancel && <div role="group" aria-label="Confirm cancellation">
        <p>Cancel order {details.order_number}? This cannot be undone. Recorded payments will remain unchanged.</p>
        <div className="fulfilment-actions">
          <button type="button" className="cancel-order" disabled={saving} onClick={() => void updateStatus("cancelled")}>Confirm cancellation</button>
          <button type="button" disabled={saving} onClick={() => setConfirmCancel(false)}>Keep order</button>
        </div>
      </div>}
      {options.length === 0 && <p>No further status changes are available for this order.</p>}
      {saving && <p role="status">Updating order status…</p>}
      {error && <p className="fulfilment-error" role="alert">{error}</p>}
      {needsRefresh && <button type="button" disabled={saving} onClick={() => void retryRefresh()}>Refresh order status</button>}
      {success && <p className="fulfilment-success" role="status">{success}</p>}
    </section>
  );
}
