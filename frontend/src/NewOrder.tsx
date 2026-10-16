
import { useEffect, useState } from "react";
import { ArrowLeft, ShoppingBag } from "lucide-react";
import {
  apiGet,
  apiSend,
  money,
} from "./lib/api";
import type {
  Product,
  NewOrderPayload,
  CreatedOrder,
} from "./lib/api";

type Props = {
  onBack: () => void;
  onCreated: (orderId: number) => void;
};

export default function NewOrder({ onBack, onCreated }: Props) {
  const [products, setProducts] = useState<Product[]>([]);
  const [productId, setProductId] = useState(0);
  const [customerName, setCustomerName] = useState("");
  const [customerPhone, setCustomerPhone] = useState("");
  const [quantity, setQuantity] = useState(1);
  const [preparation, setPreparation] = useState<"Whole" | "Chopped">("Whole");
  const [fulfilment, setFulfilment] = useState<"Pickup" | "Delivery">("Pickup");
  const [deliveryProvider, setDeliveryProvider] =
    useState<"inDrive" | "Company Rider">("inDrive");
  const [deliveryAddress, setDeliveryAddress] = useState("");
  const [deliveryFee, setDeliveryFee] = useState(0);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    apiGet<Product[]>("/api/products")
      .then((data) => {
        const available = data.filter((item) => item.available);
        setProducts(available);
        if (available.length) setProductId(available[0].id);
      })
      .catch(() => setError("Could not load products."));
  }, []);

  const product = products.find((item) => item.id === productId);
  const subtotal = (product?.price ?? 0) * quantity;
  const total = subtotal + (fulfilment === "Delivery" ? deliveryFee : 0);

  async function submitOrder(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError("");

    if (!product) {
      setError("Select an available product.");
      return;
    }

    const payload: NewOrderPayload = {
      customer_name: customerName.trim(),
      customer_phone: customerPhone.trim(),
      product_id: productId,
      quantity,
      preparation,
      fulfilment,
      delivery_provider:
        fulfilment === "Delivery" ? deliveryProvider : null,
      delivery_address:
        fulfilment === "Delivery" ? deliveryAddress.trim() : null,
      delivery_fee: fulfilment === "Delivery" ? deliveryFee : 0,
    };

    setSubmitting(true);

    try {
      const result = await apiSend<CreatedOrder>(
        "/api/orders",
        "POST",
        payload
      );
      onCreated(result.order_id);
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "Order creation failed."
      );
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <section className="new-order-panel">
      <button className="back-button" onClick={onBack} type="button">
        <ArrowLeft size={17} /> Back to dashboard
      </button>

      <div className="panel-heading">
        <div>
          <h2>Create New Order</h2>
          <p>Record a new KING'S GRILLZ customer order.</p>
        </div>
        <ShoppingBag color="#c89536" />
      </div>

      <form className="order-form" onSubmit={submitOrder}>
        <div className="form-grid">
          <label>
            Customer Name
            <input
              required
              value={customerName}
              onChange={(e) => setCustomerName(e.target.value)}
              placeholder="Enter full name"
            />
          </label>

          <label>
            Phone Number
            <input
              required
              type="tel"
              value={customerPhone}
              onChange={(e) => setCustomerPhone(e.target.value)}
              placeholder="080..."
            />
          </label>

          <label>
            Product
            <select
              value={productId}
              onChange={(e) => setProductId(Number(e.target.value))}
              required
            >
              {products.map((item) => (
                <option key={item.id} value={item.id}>
                  {item.name} — {money(item.price)}
                </option>
              ))}
            </select>
          </label>

          <label>
            Quantity
            <input
              type="number"
              min={1}
              max={100}
              required
              value={quantity}
              onChange={(e) => setQuantity(Number(e.target.value))}
            />
          </label>

          <label>
            Preparation
            <select
              value={preparation}
              onChange={(e) =>
                setPreparation(e.target.value as "Whole" | "Chopped")
              }
            >
              <option value="Whole">Whole</option>
              <option value="Chopped">Chopped</option>
            </select>
          </label>

          <label>
            Fulfilment
            <select
              value={fulfilment}
              onChange={(e) =>
                setFulfilment(e.target.value as "Pickup" | "Delivery")
              }
            >
              <option value="Pickup">Pickup</option>
              <option value="Delivery">Delivery</option>
            </select>
          </label>

          {fulfilment === "Delivery" && (
            <>
              <label>
                Delivery Provider
                <select
                  value={deliveryProvider}
                  onChange={(e) =>
                    setDeliveryProvider(
                      e.target.value as "inDrive" | "Company Rider"
                    )
                  }
                >
                  <option value="inDrive">inDrive</option>
                  <option value="Company Rider">Company Rider</option>
                </select>
              </label>

              <label>
                Delivery Fee (₦)
                <input
                  type="number"
                  min={0}
                  required
                  value={deliveryFee}
                  onChange={(e) =>
                    setDeliveryFee(Number(e.target.value))
                  }
                />
              </label>

              <label className="full-width">
                Delivery Address
                <textarea
                  required
                  rows={3}
                  value={deliveryAddress}
                  onChange={(e) => setDeliveryAddress(e.target.value)}
                  placeholder="Customer's delivery address"
                />
              </label>
            </>
          )}
        </div>

        <div className="order-total">
          <div><span>Subtotal</span><strong>{money(subtotal)}</strong></div>
          <div>
            <span>Delivery</span>
            <strong>{money(fulfilment === "Delivery" ? deliveryFee : 0)}</strong>
          </div>
          <div className="grand-total">
            <span>Total</span><strong>{money(total)}</strong>
          </div>
        </div>

        {error && <div className="error-banner">{error}</div>}

        <button
          className="create-order-button"
          type="submit"
          disabled={submitting || !product}
        >
          {submitting ? "Creating..." : "Create Order"}
        </button>
      </form>
    </section>
  );
}
