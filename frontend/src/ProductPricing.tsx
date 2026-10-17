import { useEffect, useState } from "react";
import { apiGet, apiSend, money } from "./lib/api";
import type { Product } from "./lib/api";

export default function ProductPricing() {
  const [products, setProducts] = useState<Product[]>([]);
  const [prices, setPrices] = useState<Record<number, number>>({});
  const [busy, setBusy] = useState<number | null>(null);
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");

  useEffect(() => {
    apiGet<Product[]>("/api/products")
      .then(data => {
        setProducts(data);
        const map: Record<number, number> = {};
        data.forEach(p => { map[p.id] = p.price; });
        setPrices(map);
      })
      .catch(() => setError("Could not load products."));
  }, []);

  async function save(id: number) {
    setBusy(id);
    setError("");
    setMessage("");
    try {
      const result = await apiSend<{ name: string; price: number }>(
        `/api/products/${id}/price`,
        "PATCH",
        { price: prices[id] }
      );
      setMessage(`${result.name} updated to ${money(result.price)}`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Update failed.");
    } finally {
      setBusy(null);
    }
  }

  return (
    <section className="orders-panel">
      <h2>Product Pricing</h2>
      <p>Admin only. Changes apply to new orders. Existing orders keep their historical prices.</p>
      {error && <p className="payment-error" role="alert">{error}</p>}
      {message && <p role="status">{message}</p>}
      <table>
        <thead>
          <tr><th>Product</th><th>Current Price (₦)</th><th></th></tr>
        </thead>
        <tbody>
          {products.map(p => (
            <tr key={p.id}>
              <td>{p.name}</td>
              <td>
                <input
                  type="number"
                  min={0}
                  value={prices[p.id] ?? 0}
                  onChange={e => setPrices({ ...prices, [p.id]: Number(e.target.value) })}
                />
              </td>
              <td>
                <button type="button" disabled={busy === p.id} onClick={() => void save(p.id)}>
                  {busy === p.id ? "Saving…" : "Save"}
                </button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </section>
  );
}
