import { Parcel, TrackingUpdate, Courier } from '../types';
import { demoParcels } from '../demoParcels';

// Will be replaced by deploy-all.sh — must use double quotes
export const API_URL = import.meta.env.VITE_API_URL;

export async function trackParcel(trackingNumber: string): Promise<Parcel> {
  const url = `${API_URL}/parcels/track/${trackingNumber}`;
  console.log("API_URL is:", API_URL);
  console.log("Tracking fetch URL:", url);

  const res = await fetch(url);

  const contentType = res.headers.get("content-type");
  if (!res.ok || !contentType?.includes("application/json")) {
    const text = await res.text();
    console.error("Unexpected response:", text);
    throw new Error("Failed to fetch tracking information");
  }

  return res.json();

}


export async function submitParcel(
  parcelData: Omit<Parcel, 'tracking_number' | 'tracking_history'>
): Promise<Parcel> {
  const res = await fetch(`${API_URL}/parcels`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(parcelData),
  });
  if (!res.ok) throw new Error("Failed to submit parcel");
  return res.json();
}

export async function getCouriers(): Promise<Courier[]> {
  const res = await fetch(`${API_URL}/couriers`);
  if (!res.ok) throw new Error("Failed to fetch couriers");
  return res.json();
}

export async function getParcelsByCourier(courierId: string): Promise<Parcel[]> {
  const res = await fetch(`${API_URL}/couriers/${courierId}/parcels`);
  if (!res.ok) throw new Error("Failed to fetch courier parcels");
  const data: Parcel[] = await res.json(); // Explicitly cast to Parcel[]
  return data;
}

export async function updateParcelStatus(
  trackingNumber: string,
  update: TrackingUpdate
): Promise<Parcel> {
  const res = await fetch(`${API_URL}/parcels/${trackingNumber}/status`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(update),
  });
  if (!res.ok) throw new Error("Failed to update parcel status");
  return res.json();
}

export async function loginCourier(courierId: string, password: string): Promise<Courier> {
  const res = await fetch(`${API_URL}/couriers/login`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ courier_id: courierId, password }),
  });
  if (!res.ok) {
    const message = await res.text();
    throw new Error(message || "Login failed");
  }
  return res.json();
}


export async function createTestParcel(): Promise<Parcel> {
  const res = await fetch(`${API_URL}/test/create-parcel`, {
    method: "POST",
  });
  if (!res.ok) throw new Error("Failed to create test parcel");
  return res.json();
}
export const getCustomerParcels = async (customerId: string): Promise<Parcel[]> => {
  return demoParcels.filter(
    (parcel) =>
      parcel.sender.customerId === customerId ||
      parcel.recipient.customerId === customerId
  );
};
export async function getParcels(): Promise<Parcel[]> {
  const response = await fetch("http://localhost:5000/parcels"); // adjust if needed
  if (!response.ok) {
    throw new Error("Failed to fetch parcels");
  }
  return await response.json();
}
