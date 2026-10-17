
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
  unit_price?: number;
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

function blobToBase64(blob: Blob): Promise<string> {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () => {
      const result = String(reader.result || "");
      const comma = result.indexOf(",");
      resolve(comma >= 0 ? result.slice(comma + 1) : result);
    };
    reader.onerror = () => reject(new Error("Could not read the downloaded file."));
    reader.readAsDataURL(blob);
  });
}

/** Download or share a file.
 *  Android WebView 83 cannot render PDFs and ignores <a download>.
 *  Web Share after an await is also rejected (user-gesture lost).
 *  In the Capacitor app we write the file and open the native share sheet.
 *  Desktop and web keep a normal browser download. */
export async function downloadFile(path: string, filename: string): Promise<void> {
  const response = await fetch(`${API_BASE}${path}`, {
    credentials: "same-origin",
    cache: "no-store",
  });
  if (!response.ok) {
    const contentType = response.headers.get("content-type") || "";
    if (contentType.includes("application/json")) {
      const error = await response.json().catch(() => null);
      const detail = error?.detail;
      throw new ApiError(
        typeof detail === "string" ? detail : `Download failed: ${response.status}`,
        response.status,
      );
    }
    throw new ApiError(`Download failed: ${response.status}`, response.status);
  }
  const blob = await response.blob();
  if (!blob.size) throw new Error("The server returned an empty file.");
  const type = response.headers.get("content-type") || blob.type || "application/octet-stream";

  const cap = (window as Window & { Capacitor?: { isNativePlatform?: () => boolean } }).Capacitor;
  if (cap?.isNativePlatform?.()) {
    const { Filesystem, Directory } = await import("@capacitor/filesystem");
    const { Share } = await import("@capacitor/share");
    const base64 = await blobToBase64(blob);
    const written = await Filesystem.writeFile({
      path: filename,
      data: base64,
      directory: Directory.Cache,
    });
    await Share.share({
      title: filename,
      text: filename,
      url: written.uri,
      dialogTitle: "Save or share receipt",
    });
    return;
  }

  const isAndroid = /Android/i.test(navigator.userAgent);
  if (!isAndroid) {
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = filename;
    document.body.appendChild(link);
    link.click();
    link.remove();
    setTimeout(() => URL.revokeObjectURL(url), 1000);
    return;
  }

  // Android browser (not the app): try share, otherwise explain.
  const file = new File([blob], filename, { type });
  if (typeof navigator.share === "function" && navigator.canShare?.({ files: [file] })) {
    await navigator.share({ files: [file], title: filename });
    return;
  }
  throw new Error("This Android browser cannot save the file. Use the updated app or a desktop browser.");
}
