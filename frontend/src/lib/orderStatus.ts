export type OrderStatus = "pending" | "preparing" | "ready" | "dispatched" | "completed" | "cancelled";

export type OrderStatusResponse = {
  message: string;
  order_number: string;
  previous_status: OrderStatus;
  order_status: OrderStatus;
  payment_status: string;
  balance: number;
};

// Mirrors PATCH /api/orders/{order_id}/status in backend/app/main.py.
export function allowedStatuses(status: string, fulfilment: string): OrderStatus[] {
  switch (status) {
    case "pending": return ["preparing", "cancelled"];
    case "preparing": return ["ready", "cancelled"];
    case "ready": return fulfilment === "Delivery"
      ? ["dispatched", "completed", "cancelled"]
      : ["completed", "cancelled"];
    case "dispatched": return ["completed"];
    default: return [];
  }
}

export function statusAction(status: OrderStatus, fulfilment: string): string {
  switch (status) {
    case "preparing": return "Start preparing";
    case "ready": return fulfilment === "Pickup" ? "Ready for pickup" : "Ready for delivery";
    case "dispatched": return "Dispatch delivery";
    case "completed": return fulfilment === "Pickup" ? "Mark collected" : "Mark delivered";
    case "cancelled": return "Cancel order";
    default: return "Pending";
  }
}
