
import { useEffect, useState } from "react";
import { API_BASE, apiGet, apiSend, money } from "./lib/api";

type Payment = {
  payment_id: number;
  amount: number;
  method: string;
  reference: string;
  status: string;
  created_at: string;
};

type PaymentHistory = {
  payments: Payment[];
};

type Props = {
  orderId: number;
  balance: number;
  canRecordPayments: boolean;
  onPaymentRecorded: () => Promise<void>;
};

export default function PaymentPanel({
  orderId,
  balance,
  canRecordPayments,
  onPaymentRecorded,
}: Props) {
  const [amount, setAmount] = useState<string | null>(null);
  const [method, setMethod] = useState("PalmPay");
  const [reference, setReference] = useState("");
  const [payments, setPayments] = useState<Payment[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");

  async function loadPayments() {
    try {
      const result = await apiGet<PaymentHistory | Payment[]>(
        `/api/orders/${orderId}/payments`
      );
      setPayments(Array.isArray(result) ? result : result.payments ?? []);
    } catch {
      setError("Could not load payment history.");
    }
  }

  useEffect(() => {
    let active = true;
    apiGet<PaymentHistory>(`/api/orders/${orderId}/payments`)
      .then(result => { if (active) setPayments(result.payments); })
      .catch(() => { if (active) setError("Could not load payment history."); });
    return () => { active = false; };
  }, [orderId, balance]);

  async function recordPayment(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (loading || !canRecordPayments) return;
    setError("");
    setSuccess("");

    const value = Number(amount ?? balance);

    if (!Number.isSafeInteger(value) || value <= 0 || value > balance) {
      setError("Enter a whole-naira amount greater than zero and not above the balance.");
      return;
    }

    if (reference.trim().length < 3) {
      setError("Enter a unique payment reference of at least 3 characters.");
      return;
    }

    if (
      !window.confirm(
        `Have you independently verified receipt of ${money(value)} via ${method}?`
      )
    ) {
      return;
    }

    setLoading(true);

    try {
      await apiSend(
        `/api/orders/${orderId}/payments`,
        "POST",
        {
          amount: value,
          method,
          reference: reference.trim(),
        }
      );

      setSuccess("Verified payment recorded successfully.");
      setReference("");
      setAmount(null);
      await onPaymentRecorded();
      await loadPayments();
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "Payment could not be recorded."
      );
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="payment-panel">
      <h3>Payment Management</h3>

      <p>
        Outstanding balance: <strong>{money(balance)}</strong>
      </p>

      {balance > 0 && !canRecordPayments ? (
        <p>A cashier or administrator must record payments.</p>
      ) : balance > 0 ? (
        <form onSubmit={recordPayment} className="payment-form">
          <label>
            Verified Amount (₦)
            <input
              type="number"
              min="1"
              step="1"
              max={balance}
              required
              value={amount ?? String(Math.max(0, balance))}
              onChange={(event) => setAmount(event.target.value)}
            />
          </label>

          <label>
            Payment Method
            <select
              value={method}
              onChange={(event) => setMethod(event.target.value)}
            >
              <option value="PalmPay">PalmPay</option>
              <option value="Bank Transfer">Bank Transfer</option>
              <option value="Cash">Cash</option>
              <option value="POS">POS</option>
            </select>
          </label>

          <label>
            Transaction Reference
            <input
              required
              minLength={3}
              maxLength={100}
              value={reference}
              onChange={(event) => setReference(event.target.value)}
              placeholder="Unique transaction ID"
            />
          </label>

          <button type="submit" disabled={loading}>
            {loading ? "Recording..." : "Record Verified Payment"}
          </button>
        </form>
      ) : (
        <p className="payment-success">Order fully paid.</p>
      )}

      {error && <p className="payment-error">{error}</p>}
      {success && <p className="payment-success">{success}</p>}

      <h4>Payment History</h4>

      {payments.length === 0 ? (
        <p>No payments recorded yet.</p>
      ) : (
        <div className="payment-history">
          {payments.map((payment) => (
            <div className="payment-entry" key={payment.payment_id}>
              <div>
                <strong>{money(payment.amount)}</strong>
                <small>
                  {payment.method} · {payment.reference}
                </small>
              </div>

              <a
                href={`${API_BASE}/api/payments/${payment.payment_id}/receipt`}
                target="_blank"
                rel="noreferrer"
              >
                PDF Receipt
              </a>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
