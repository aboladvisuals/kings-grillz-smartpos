
// Same-origin requests keep session cookies on the frontend host, including PDFs.
export const API_BASE = "";

export type Staff = {
  id: number;
  username: string;
  role: "admin" | "cashier" | "operations";
  can_record_payments: boolean;
};
export type StaffSession = { staff: Staff; csrf_token: string };
let csrfToken: string | null = null;
export function setCsrfToken(token: string | null) { csrfToken = token; }

export class ApiError extends Error {
  status: number;
  constructor(message: string, status: number) { super(message); this.status = status; }
}

async function readResponse<T>(response: Response): Promise<T> {
  const contentType = response.headers.get("content-type") || "";
  const isJson = contentType.includes("application/json");

  if (!response.ok) {
    if (response.status === 401) {
      csrfToken = null;
      window.dispatchEvent(new Event("staff-session-expired"));
    }
    let message = `Request failed: ${response.status}`;
    if (isJson) {
      const error = await response.json().catch(() => null);
      const detail = error?.detail;
      message = typeof detail === "string" ? detail : Array.isArray(detail)
        ? detail.map((item: { msg?: string }) => item.msg ?? "Invalid input").join(". ")
        : message;
    } else {
      // Non-JSON (likely HTML from wrong origin or proxy failure)
      const text = await response.text().catch(() => "");
      if (text.trim().startsWith("<!doctype") || text.trim().startsWith("<html")) {
        message = "Received HTML instead of API response. Check network or app configuration.";
      }
    }
    throw new ApiError(message, response.status);
  }
  if (response.status === 204) return undefined as T;
  if (!isJson) {
    const text = await response.text().catch(() => "");
    if (text.trim().startsWith("<!doctype") || text.trim().startsWith("<html")) {
      throw new ApiError("Received HTML instead of API response. The app may be loading from the wrong origin.", response.status);
    }
    throw new ApiError("Expected JSON response but received non-JSON content.", response.status);
  }
  return response.json() as Promise<T>;
}

export type Order = {
  id: number;
  order_number: string;
  customer_id: number;
  quantity: number;
  preparation: string;
  fulfilment: string;
  subtotal: number;
  delivery_fee: number;
  total: number;
  amount_paid: number;
  balance: number;
  payment_status: string;
  order_status: string;
  created_at: string;
};

export type OrderDetails = {
  order_number: string;
  customer_name: string;
  customer_phone: string;
  quantity: number;
  unit_price: number;
  preparation: string;
  fulfilment: string;
  delivery_provider: string | null;
  delivery_address: string | null;
  subtotal: number;
  delivery_fee: number;
  total: number;
  amount_paid: number;
  balance: number;
  payment_status: string;
  order_status: string;
  created_at: string;
};

export async function apiGet<T>(path: string): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, { credentials: "same-origin", cache: "no-store" });
  return readResponse<T>(response);
}

export async function apiSend<T>(
  path: string,
  method: "POST" | "PATCH",
  body: unknown
): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, {
    method,
    credentials: "same-origin",
    cache: "no-store",
    headers: {
      "Content-Type": "application/json",
      ...(csrfToken ? { "X-CSRF-Token": csrfToken } : {}),
    },
    body: JSON.stringify(body),
  });

  return readResponse<T>(response);
}

export function money(value: number): string {
  return `₦${value.toLocaleString("en-NG")}`;
}


export type Product = {
  id: number;
  name: string;
  price: number;
  currency: string;
  available: boolean;
  preparation_options: string[];
};

export type NewOrderPayload = {
  customer_name: string;
  customer_phone: string;
  product_id: number;
  quantity: number;
  preparation: "Whole" | "Chopped";
  fulfilment: "Pickup" | "Delivery";
  delivery_provider?: "inDrive" | "Company Rider" | null;
  delivery_address?: string | null;
  delivery_fee: number;
};

export type CreatedOrder = {
  message: string;
  order_id: number;
  order_number: string;
  customer: string;
  quantity: number;
  unit_price: number;
  subtotal: number;
  delivery_fee: number;
  total: number;
  payment_status: string;
  order_status: string;
};
