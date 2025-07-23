/*
 * =================================================================
 * File: /frontend/app/page.js (Updated with SSE for live updates)
 * =================================================================
 */
"use client";

import { useState, useEffect, useCallback } from "react";

const API_URL = "http://localhost:8000";
const ITEM_ID = "charizard-1st-ed";

export default function HomePage() {
  const [item, setItem] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [message, setMessage] = useState({ text: "", type: "" });
  const [error, setError] = useState(null);

  // Initial fetch function remains the same
  const fetchItemStatus = useCallback(async () => {
    try {
      const response = await fetch(`${API_URL}/status/${ITEM_ID}`);
      if (!response.ok) throw new Error("Network response was not ok");
      const data = await response.json();
      setItem(data);
      setError(null);
    } catch (error) {
      console.error("Failed to fetch item status:", error);
      setError("Could not connect to the backend. Is it running?");
      setItem(null);
    }
  }, []);

  // Fetch the initial status when the component mounts
  useEffect(() => {
    fetchItemStatus();
  }, [fetchItemStatus]);

  // *** NEW: useEffect for Server-Sent Events ***
  useEffect(() => {
    // The EventSource API is built into modern browsers.
    // It keeps a persistent connection to the server.
    const eventSource = new EventSource(`${API_URL}/events`);

    // This function is called whenever the server sends a message
    eventSource.onmessage = (event) => {
      console.log("Received SSE update:", event.data);
      const updatedItem = JSON.parse(event.data);
      // Update the component's state with the new data from the server
      setItem(updatedItem);
    };

    // Handle any errors with the connection
    eventSource.onerror = (err) => {
      console.error("EventSource failed:", err);
      // You might want to add logic here to try and reconnect
    };

    // This cleanup function is crucial. It runs when the component
    // unmounts, closing the connection to prevent memory leaks.
    return () => {
      eventSource.close();
    };
  }, []); // The empty dependency array means this runs once on mount.

  const handleBuy = async () => {
    setIsLoading(true);
    setMessage({ text: "", type: "" });
    try {
      const response = await fetch(`${API_URL}/buy/${ITEM_ID}`, {
        method: "POST",
      });
      const data = await response.json();
      if (response.ok) {
        setMessage({ text: `Success! ${data.message}`, type: "success" });
      } else {
        setMessage({ text: `Failed: ${data.detail}`, type: "error" });
      }
    } catch (error) {
      setMessage({ text: "An unexpected error occurred.", type: "error" });
    } finally {
      // We no longer need to manually fetch status here,
      // as the SSE will push the update automatically.
      setIsLoading(false);
    }
  };

  const handleReset = async () => {
    setIsLoading(true);
    setMessage({ text: "", type: "" });
    try {
      await fetch(`${API_URL}/reset`, { method: "POST" });
      setMessage({ text: "Demo has been reset.", type: "info" });
    } catch (error) {
      setMessage({ text: "Could not reset demo state.", type: "error" });
    } finally {
      setIsLoading(false);
    }
  };

  // ... The rest of the JSX rendering code is identical ...
  if (error) {
    return (
      <main className="flex items-center justify-center min-h-screen bg-gray-100">
        <div className="text-center p-8 bg-white rounded-lg shadow-md">
          <h1 className="text-2xl font-bold text-red-600">Connection Error</h1>
          <p className="mt-2 text-gray-700">{error}</p>
        </div>
      </main>
    );
  }

  if (!item) {
    return (
      <main className="flex items-center justify-center min-h-screen bg-gray-100">
        <p className="text-lg text-gray-600">Loading item details...</p>
      </main>
    );
  }

  return (
    <main className="flex flex-col items-center justify-center min-h-screen bg-gray-900 text-white p-4 font-sans">
      <div className="w-full max-w-sm bg-gray-800 border border-gray-700 rounded-2xl shadow-lg overflow-hidden">
        <div className="p-6">
          <h1 className="text-2xl font-bold text-center text-cyan-400">
            Misprint PoC Demo
          </h1>
          <p className="text-sm text-center text-gray-400 mb-6">
            Concurrency Test (Live)
          </p>
        </div>
        <img
          src={item.image_url}
          alt={item.name}
          className="w-full h-auto object-cover"
          onError={(e) => {
            e.target.onerror = null;
            e.target.src =
              "https://placehold.co/400x600/2D3748/E2E8F0?text=Image+Not+Found";
          }}
        />
        <div className="p-6">
          <h2 className="text-xl font-bold">{item.name}</h2>
          <p className="text-gray-400 mt-1">{item.description}</p>
          <div
            className={`mt-4 text-lg font-semibold py-2 px-4 rounded-md text-center transition-colors duration-300 ${
              item.quantity > 0
                ? "bg-green-500/20 text-green-400"
                : "bg-red-500/20 text-red-400"
            }`}
          >
            Quantity Available: {item.quantity}
          </div>
          {message.text && (
            <div
              className={`mt-4 text-center p-3 rounded-lg text-sm ${
                message.type === "success" ? "bg-green-500/90 text-white" : ""
              } ${message.type === "error" ? "bg-red-500/90 text-white" : ""} ${
                message.type === "info" ? "bg-blue-500/90 text-white" : ""
              }`}
            >
              {message.text}
            </div>
          )}
          <div className="mt-6 flex flex-col gap-4">
            <button
              onClick={handleBuy}
              disabled={isLoading || item.quantity === 0}
              className="w-full px-4 py-3 text-base font-bold text-white bg-blue-600 rounded-lg hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-opacity-50 transition-colors disabled:bg-gray-600 disabled:cursor-not-allowed"
            >
              {isLoading ? "Processing..." : "Buy Now"}
            </button>
            <button
              onClick={handleReset}
              disabled={isLoading}
              className="w-full px-4 py-2 text-sm font-bold text-gray-300 bg-gray-700 rounded-lg hover:bg-gray-600 focus:outline-none focus:ring-2 focus:ring-gray-500 focus:ring-opacity-50 transition-colors disabled:bg-gray-500"
            >
              {isLoading ? "Resetting..." : "Reset Demo"}
            </button>
          </div>
        </div>
      </div>
      <footer className="text-center mt-8 text-gray-500 text-sm">
        <p>Run the test script to see the quantity update here in real-time.</p>
      </footer>
    </main>
  );
}
