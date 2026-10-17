
import { useEffect, useState } from "react";
import {
  LayoutDashboard, ShoppingBag, Wallet, RefreshCw,
  FileText, MessageCircle, Flame, TrendingUp,
  Clock, CheckCircle2, Plus
} from "lucide-react";
import { apiGet, money, API_BASE } from "./lib/api";
import type { Order, OrderDetails, Staff } from "./lib/api";
import NewOrder from "./NewOrder";
import PaymentPanel from "./PaymentPanel";
import OrderStatusPanel from "./OrderStatusPanel";
import ProductPricing from "./ProductPricing";
import "./App.css";

type Section = "dashboard" | "orders" | "payments" | "new-order" | "pricing";

export default function App({ staff }: { staff: Staff }) {
  const [orders, setOrders] = useState<Order[]>([]);
  const [section, setSection] = useState<Section>("dashboard");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [selectedOrder, setSelectedOrder] = useState<{
    id: number;
    details: OrderDetails;
  } | null>(null);

  async function loadOrders() {
    setLoading(true);
    setError("");
    try {
      setOrders(await apiGet<Order[]>("/api/orders"));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to load orders.");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    let active = true;
    apiGet<Order[]>("/api/orders")
      .then(data => { if (active) setOrders(data); })
      .catch(err => { if (active) setError(err instanceof Error ? err.message : "Unable to load orders."); })
      .finally(() => { if (active) setLoading(false); });
    return () => { active = false; };
  }, []);

  const totalSales = orders.reduce((s, o) => s + o.total, 0);
  const totalReceived = orders.reduce((s, o) => s + o.amount_paid, 0);
  const outstanding = orders.reduce(
    (s, o) => s + (o.balance ?? o.total - o.amount_paid), 0
  );
  const activeOrders = orders.filter(
    o => !["completed", "cancelled"].includes(o.order_status)
  ).length;

  async function openOrder(id: number) {
    try {
      const details = await apiGet<OrderDetails>(`/api/orders/${id}`);
      setSelectedOrder({ id, details });
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to open order.");
    }
  }

  async function refreshSelectedOrder() {
    if (!selectedOrder) return;
    await loadOrders();
    await openOrder(selectedOrder.id);
  }

  function handleStatusChanged(id: number, order_status: string) {
    setOrders(current => current.map(order => order.id === id ? { ...order, order_status } : order));
    setSelectedOrder(current => current?.id === id
      ? { ...current, details: { ...current.details, order_status } }
      : current);
  }

  async function openWhatsApp(id: number) {
    try {
      const result = await apiGet<{ whatsapp_url: string }>(
        `/api/orders/${id}/whatsapp`
      );
      const link = document.createElement("a");
      link.href = result.whatsapp_url;
      link.target = "_blank";
      link.rel = "noopener noreferrer";
      document.body.appendChild(link);
      link.click();
      link.remove();
    } catch (err) {
      setError(err instanceof Error ? err.message : "WhatsApp unavailable.");
    }
  }

  async function handleOrderCreated(id: number) {
    setSection("orders");
    await loadOrders();
    await openOrder(id);
  }

  const visibleOrders = section === "payments"
    ? orders.filter(o => o.amount_paid > 0)
    : orders;

  const title = section === "dashboard" ? "Dashboard"
    : section === "orders" ? "Order Management"
    : section === "payments" ? "Payment Overview"
    : section === "pricing" ? "Product Pricing" : "Create New Order";

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <div className="brand">
          <img src="/logo.png" alt="" style={{width: 48, height: 48, borderRadius: "50%"}} />
          <div><strong>KING'S GRILLZ</strong><span>SMARTPOS</span></div>
        </div>

        <div className="sidebar-label">WORKSPACE</div>

        <nav className="navigation">
          <button
            className={section === "dashboard" ? "active" : ""}
            onClick={() => setSection("dashboard")}
          >
            <LayoutDashboard size={19} /> Dashboard
          </button>
          <button
            className={section === "new-order" ? "active" : ""}
            onClick={() => setSection("new-order")}
          >
            <Plus size={19} /> New Order
          </button>
          <button
            className={section === "orders" ? "active" : ""}
            onClick={() => setSection("orders")}
          >
            <ShoppingBag size={19} /> Orders
          </button>
          <button
            className={section === "payments" ? "active" : ""}
            onClick={() => setSection("payments")}
          >
            <Wallet size={19} /> Payments
          </button>
          {staff.role === "admin" && (
            <button
              className={section === "pricing" ? "active" : ""}
              onClick={() => setSection("pricing")}
            >
              <Wallet size={19} /> Pricing
            </button>
          )}
        </nav>

        <div className="sidebar-bottom">
          <Flame size={20} />
          <div>
            <strong>Your Premium Awo Plug</strong>
            <span>Powered by KING'S GRILLZ</span>
          </div>
        </div>
      </aside>

      <main className="main-content">
        <header className="topbar">
          <div>
            <span className="eyebrow">KING'S GRILLZ SMARTPOS</span>
            <h1>{title}</h1>
            <p>Manage customer orders, payments and invoices.</p>
          </div>
          {section !== "new-order" && (
            <button
              className="refresh-button"
              onClick={() => void loadOrders()}
              disabled={loading}
            >
              <RefreshCw size={17} /> Refresh
            </button>
          )}
        </header>

        {error && <div className="error-banner">{error}</div>}

        {section === "pricing" && staff.role === "admin" ? (
          <ProductPricing />
        ) : section === "new-order" ? (
          <NewOrder
            onBack={() => setSection("dashboard")}
            onCreated={id => { void handleOrderCreated(id); }}
          />
        ) : (
          <>
            <section className="stats-grid">
              <div className="stat-card">
                <div className="stat-heading">
                  <span>Total Order Value</span><TrendingUp size={20} />
                </div>
                <strong>{money(totalSales)}</strong>
                <small>All recorded orders</small>
              </div>
              <div className="stat-card">
                <div className="stat-heading">
                  <span>Payments Received</span><Wallet size={20} />
                </div>
                <strong>{money(totalReceived)}</strong>
                <small>Recorded payments</small>
              </div>
              <div className="stat-card">
                <div className="stat-heading">
                  <span>Outstanding Balance</span><Clock size={20} />
                </div>
                <strong>{money(outstanding)}</strong>
                <small>Unpaid customer balances</small>
              </div>
              <div className="stat-card">
                <div className="stat-heading">
                  <span>Active Orders</span><CheckCircle2 size={20} />
                </div>
                <strong>{activeOrders}</strong>
                <small>Orders awaiting completion</small>
              </div>
            </section>

            <section className="orders-panel">
              <div className="panel-heading">
                <div>
                  <h2>
                    {section === "payments"
                      ? "Orders With Payments"
                      : "Recent Orders"}
                  </h2>
                  <p>Live records from your KING'S GRILLZ database</p>
                </div>
                <span className="record-count">
                  {visibleOrders.length} records
                </span>
              </div>

              <div className="table-scroll">
                <table>
                  <thead>
                    <tr>
                      <th>ORDER</th><th>QTY</th><th>TOTAL</th>
                      <th>PAID</th><th>BALANCE</th><th>STATUS</th>
                      <th>ACTIONS</th>
                    </tr>
                  </thead>
                  <tbody>
                    {loading ? (
                      <tr><td colSpan={7}>Loading orders...</td></tr>
                    ) : visibleOrders.length === 0 ? (
                      <tr><td colSpan={7}>No orders found.</td></tr>
                    ) : visibleOrders.map(order => (
                      <tr key={order.id}>
                        <td>
                          <button
                            className="order-link"
                            onClick={() => void openOrder(order.id)}
                          >
                            {order.order_number}
                          </button>
                        </td>
                        <td>{order.quantity}</td>
                        <td>{money(order.total)}</td>
                        <td>{money(order.amount_paid)}</td>
                        <td>{money(
                          order.balance ?? order.total - order.amount_paid
                        )}</td>
                        <td>
                          <span className={`status-pill ${order.order_status}`}>
                            {order.order_status}
                          </span>
                        </td>
                        <td>
                          <div className="row-actions">
                            <a
                              title="Download invoice PDF"
                              href={`${API_BASE}/api/orders/${order.id}/invoice`}
                              target="_blank"
                              rel="noreferrer"
                            >
                              <FileText size={17} />
                            </a>
                            <a
                              title="Download invoice picture"
                              href={`${API_BASE}/api/orders/${order.id}/invoice.png`}
                              target="_blank"
                              rel="noreferrer"
                            >
                              <FileText size={17} />
                            </a>
                            <button
                              title="Share via WhatsApp"
                              onClick={() => void openWhatsApp(order.id)}
                            >
                              <MessageCircle size={17} />
                            </button>
                          </div>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </section>
          </>
        )}

        {selectedOrder && (
          <div
            className="modal-overlay"
            onClick={() => setSelectedOrder(null)}
          >
            <div
              className="order-modal"
              onClick={event => event.stopPropagation()}
            >
              <button
                className="modal-close"
                onClick={() => setSelectedOrder(null)}
                aria-label="Close"
              >
                ×
              </button>

              <span className="eyebrow">ORDER DETAILS</span>
              <h2>{selectedOrder.details.order_number}</h2>

              {[
                ["Customer", selectedOrder.details.customer_name],
                ["Phone", selectedOrder.details.customer_phone],
                ["Quantity", selectedOrder.details.quantity],
                ["Preparation", selectedOrder.details.preparation],
                ["Fulfilment", selectedOrder.details.fulfilment],
                ["Order Status", selectedOrder.details.order_status],
                ["Payment Status", selectedOrder.details.payment_status],
                ["Total", money(selectedOrder.details.total)],
                ["Amount Paid", money(selectedOrder.details.amount_paid)],
                ["Balance Due", money(selectedOrder.details.balance)],
              ].map(([label, value]) => (
                <div className="detail-line" key={String(label)}>
                  <span>{label}</span>
                  <strong>{value}</strong>
                </div>
              ))}

              <OrderStatusPanel
                key={`status-${selectedOrder.id}`}
                orderId={selectedOrder.id}
                details={selectedOrder.details}
                onStatusChanged={handleStatusChanged}
              />

              <PaymentPanel
                key={`payment-${selectedOrder.id}`}
                orderId={selectedOrder.id}
                balance={selectedOrder.details.balance}
                canRecordPayments={staff.can_record_payments}
                onPaymentRecorded={refreshSelectedOrder}
              />
            </div>
          </div>
        )}
      </main>
    </div>
  );
}
