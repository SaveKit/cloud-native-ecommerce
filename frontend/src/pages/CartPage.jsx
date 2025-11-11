import React, { useState, useEffect } from 'react';
import { fetchAuthSession } from 'aws-amplify/auth';

const API_ENDPOINT = import.meta.env.VITE_API_ENDPOINT;

function CartPage() {
    const [cartItems, setCartItems] = useState([]); // { product, quantity }
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);
    const [orderSuccess, setOrderSuccess] = useState(false);

    // ดึงข้อมูลสินค้าในตะกร้าจาก Local Storage (หรือ Context)
    useEffect(() => {
        const storedCart = JSON.parse(localStorage.getItem('cart')) || {};
        // ตรงนี้คุณต้อง fetch Product details อีกครั้งจาก API เพื่อเอา Price ล่าสุด
        // สำหรับ PoC เราจะ mock ข้อมูลสินค้าสมมติขึ้นมา
        const mockProducts = [
            { ProductID: "PROD-1", Name: "Fancy Widget", Price: 10.50, ImageURL: "https://via.placeholder.com/100x70?text=Widget1" },
            { ProductID: "PROD-2", Name: "Super Gadget", Price: 25.00, ImageURL: "https://via.placeholder.com/100x70?text=Gadget1" },
            // ... เพิ่มสินค้า mock อื่นๆ ที่มีอยู่ใน DB
        ];

        const items = Object.keys(storedCart).map(productID => {
            const product = mockProducts.find(p => p.ProductID === productID);
            return product ? { product, quantity: storedCart[productID] } : null;
        }).filter(Boolean); // กรอง null ออก

        setCartItems(items);
    }, []);

    const updateQuantity = (productID, delta) => {
        setCartItems(prevItems => {
            const newItems = prevItems.map(item => 
                item.product.ProductID === productID 
                    ? { ...item, quantity: Math.max(0, item.quantity + delta) } 
                    : item
            ).filter(item => item.quantity > 0);

            // อัปเดต Local Storage
            const newStoredCart = newItems.reduce((acc, item) => {
                acc[item.product.ProductID] = item.quantity;
                return acc;
            }, {});
            localStorage.setItem('cart', JSON.stringify(newStoredCart));
            return newItems;
        });
    };

    const removeItem = (productID) => {
        setCartItems(prevItems => {
            const newItems = prevItems.filter(item => item.product.ProductID !== productID);
            const newStoredCart = newItems.reduce((acc, item) => {
                acc[item.product.ProductID] = item.quantity;
                return acc;
            }, {});
            localStorage.setItem('cart', JSON.stringify(newStoredCart));
            return newItems;
        });
    };

    const calculateTotal = () => {
        return cartItems.reduce((total, item) => total + (item.product.Price * item.quantity), 0);
    };

    const handleCheckout = async () => {
        if (cartItems.length === 0) {
            alert("Your cart is empty!");
            return;
        }

        setLoading(true);
        setError(null);
        setOrderSuccess(false);

        try {
            const session = await fetchAuthSession();
            const jwtToken = session.tokens?.idToken?.toString();
            
            if (!jwtToken) {
                throw new Error("No IdToken found.");
            }

            const orderItems = cartItems.map(item => ({
                ProductID: item.product.ProductID,
                Quantity: item.quantity,
                PricePerUnit: item.product.Price // ใช้ Price จากสินค้า
            }));
            const totalAmount = calculateTotal();

            const response = await fetch(`${API_ENDPOINT}/orders`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    Authorization: `Bearer ${jwtToken}`,
                },
                body: JSON.stringify({
                    Items: orderItems,
                    TotalAmount: totalAmount
                }),
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const orderResponse = await response.json();
            console.log("Order placed successfully:", orderResponse);
            setOrderSuccess(true);
            setCartItems([]); // ล้างตะกร้า
            localStorage.removeItem('cart'); // ล้าง Local Storage
        } catch (err) {
            console.error("Failed to place order:", err);
            setError("Failed to place order. Please try again.");
        } finally {
            setLoading(false);
        }
    };

    if (orderSuccess) {
        return (
            <div className="bg-green-100 border-l-4 border-green-500 text-green-700 p-4 mb-4" role="alert">
                <p className="font-bold">Order Placed!</p>
                <p>Your order has been placed successfully. Thank you for your purchase!</p>
                <button 
                    onClick={() => setOrderSuccess(false)}
                    className="mt-2 bg-green-600 hover:bg-green-700 text-white font-bold py-2 px-4 rounded"
                >
                    Continue Shopping
                </button>
            </div>
        );
    }

    if (cartItems.length === 0) {
        return <div className="text-center text-gray-700 p-8">Your cart is empty!</div>;
    }

    return (
        <div className="p-4">
            <h1 className="text-3xl font-bold text-gray-800 mb-6 text-center">Your Shopping Cart</h1>
            {error && <div className="bg-red-100 border-l-4 border-red-500 text-red-700 p-4 mb-4" role="alert">{error}</div>}

            <div className="bg-white rounded-lg shadow-md p-6">
                {cartItems.map(item => (
                    <div key={item.product.ProductID} className="flex items-center justify-between border-b py-4 last:border-b-0">
                        <div className="flex items-center space-x-4">
                            <img src={item.product.ImageURL} alt={item.product.Name} className="w-16 h-16 object-cover rounded" />
                            <div>
                                <h3 className="font-semibold text-gray-900">{item.product.Name}</h3>
                                <p className="text-gray-600">${item.product.Price.toFixed(2)} each</p>
                            </div>
                        </div>
                        <div className="flex items-center space-x-4">
                            <div className="flex items-center border rounded-md">
                                <button 
                                    onClick={() => updateQuantity(item.product.ProductID, -1)} 
                                    className="px-3 py-1 bg-gray-200 hover:bg-gray-300 rounded-l-md"
                                >-</button>
                                <span className="px-3">{item.quantity}</span>
                                <button 
                                    onClick={() => updateQuantity(item.product.ProductID, 1)} 
                                    className="px-3 py-1 bg-gray-200 hover:bg-gray-300 rounded-r-md"
                                >+</button>
                            </div>
                            <span className="text-lg font-semibold text-gray-800">${(item.product.Price * item.quantity).toFixed(2)}</span>
                            <button 
                                onClick={() => removeItem(item.product.ProductID)} 
                                className="text-red-500 hover:text-red-700"
                            >Remove</button>
                        </div>
                    </div>
                ))}

                <div className="mt-6 pt-4 border-t flex justify-between items-center">
                    <span className="text-xl font-bold text-gray-900">Total:</span>
                    <span className="text-2xl font-bold text-blue-700">${calculateTotal().toFixed(2)}</span>
                </div>

                <button 
                    onClick={handleCheckout} 
                    disabled={loading}
                    className="w-full bg-blue-600 text-white font-bold py-3 rounded-lg mt-6 hover:bg-blue-700 transition-colors duration-200 disabled:opacity-50"
                >
                    {loading ? 'Processing...' : 'Proceed to Checkout'}
                </button>
            </div>
        </div>
    );
}

export default CartPage;