// frontend/src/pages/OrderHistoryPage.jsx
import React, { useState, useEffect } from 'react';
import { fetchAuthSession } from 'aws-amplify/auth';

const API_ENDPOINT = import.meta.env.VITE_API_ENDPOINT;

function OrderHistoryPage() {
    const [orders, setOrders] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);

    useEffect(() => {
        const fetchOrderHistory = async () => {
            setLoading(true);
            setError(null);
            try {
                const session = await fetchAuthSession();
                const jwtToken = session.tokens?.idToken?.toString();

                if (!jwtToken) {
                    throw new Error("No IdToken found. Please sign in again.");
                }

                // --- นี่คือการเรียก Service ที่เหลืออยู่! ---
                const response = await fetch(`${API_ENDPOINT}/orders`, {
                    method: 'GET',
                    headers: {
                        Authorization: `Bearer ${jwtToken}`,
                    },
                });
                // ---

                if (!response.ok) {
                    throw new Error(`HTTP error! status: ${response.status}`);
                }
                const data = await response.json();
                setOrders(data);
            } catch (err) {
                console.error("Failed to fetch order history:", err);
                setError("Failed to fetch order history. Please try again.");
            } finally {
                setLoading(false);
            }
        };

        fetchOrderHistory();
    }, []);

    if (loading) return <div className="text-center text-gray-700 p-8">Loading your order history...</div>;
    if (error) return <div className="text-center text-red-600 p-8">{error}</div>;

    return (
        <div className="p-4 max-w-4xl mx-auto">
            <h1 className="text-3xl font-bold text-gray-800 mb-6 text-center">Your Order History</h1>
            {orders.length === 0 ? (
                <p className="text-center text-gray-500">You have not placed any orders yet.</p>
            ) : (
                <div className="space-y-6">
                    {orders.map(order => (
                        <div key={order.OrderID} className="bg-white rounded-lg shadow-md p-6">
                            <div className="flex justify-between items-start mb-4">
                                <div>
                                    <h2 className="text-xl font-semibold text-blue-700">Order ID: {order.OrderID}</h2>
                                    <p className="text-sm text-gray-500">
                                        Placed on: {new Date(order.CreatedAt).toLocaleString()}
                                    </p>
                                </div>
                                <span className={`px-3 py-1 rounded-full text-sm font-semibold ${
                                    order.Status === 'PENDING' ? 'bg-yellow-200 text-yellow-800' : 'bg-green-200 text-green-800'
                                }`}>
                                    {order.Status}
                                </span>
                            </div>
                            <div className="border-t border-b py-2 mb-4">
                                {order.Items.map(item => (
                                    <div key={item.ProductID} className="flex justify-between items-center py-1">
                                        <span className="text-gray-700">{item.ProductID} (x{item.Quantity})</span>
                                        <span className="text-gray-800">${(item.PricePerUnit * item.Quantity).toFixed(2)}</span>
                                    </div>
                                ))}
                            </div>
                            <div className="text-right">
                                <span className="text-lg font-bold text-gray-900">Total: ${order.TotalAmount.toFixed(2)}</span>
                            </div>
                        </div>
                    ))}
                </div>
            )}
        </div>
    );
}

export default OrderHistoryPage;