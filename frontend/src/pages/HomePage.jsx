import React, { useEffect, useState } from 'react';
import { fetchAuthSession } from 'aws-amplify/auth';
import { FaShoppingCart } from 'react-icons/fa'; // ไอคอนตะกร้า

const API_ENDPOINT = import.meta.env.VITE_API_ENDPOINT; // ดึงจาก .env

function HomePage() {
    const [products, setProducts] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [cart, setCart] = useState({}); // { productID: quantity }

    useEffect(() => {
        const fetchProducts = async () => {
            try {
                setLoading(true);
                setError(null);

                // ดึง JWT Token
                const session = await fetchAuthSession();
                const jwtToken = session.tokens?.idToken?.toString();

                if (!jwtToken) {
                    throw new Error("No IdToken found. Please sign in again.");
                }

                const response = await fetch(`${API_ENDPOINT}/products`, {
                    headers: {
                        Authorization: `Bearer ${jwtToken}`,
                    },
                });

                if (!response.ok) {
                    throw new Error(`HTTP error! status: ${response.status}`);
                }
                const data = await response.json();
                setProducts(data);
            } catch (err) {
                console.error("Failed to fetch products:", err);
                setError("Failed to fetch products. Please try again.");
            } finally {
                setLoading(false);
            }
        };

        fetchProducts();
    }, []); // รันครั้งเดียวเมื่อ Component โหลด

    const addToCart = (product) => {
        setCart(prevCart => ({
            ...prevCart,
            [product.ProductID]: (prevCart[product.ProductID] || 0) + 1
        }));
        alert(`${product.Name} added to cart!`);
    };

    if (loading) return <div className="text-center text-gray-700">Loading products...</div>;
    if (error) return <div className="text-center text-red-600">{error}</div>;

    return (
        <div className="p-4">
            <h1 className="text-3xl font-bold text-gray-800 mb-6 text-center">Our Products</h1>
            <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-6">
                {products.map(product => (
                    <div key={product.ProductID} className="bg-white rounded-lg shadow-md overflow-hidden transform hover:scale-105 transition-transform duration-300">
                        {/* รูปภาพสินค้า (ใช้ URL จาก DB เหมือนเดิม) */}
                        <img 
                            src={product.ImageURL || 'https://via.placeholder.com/300x200?text=No+Image'} 
                            alt={product.Name} 
                            className="w-full h-48 object-cover" 
                        />
                        <div className="p-4">
                            <h2 className="text-xl font-semibold text-gray-900 mb-2">{product.Name}</h2>
                            <p className="text-gray-600 text-sm mb-3 line-clamp-2">{product.Description}</p>
                            <div className="flex justify-between items-center mt-4">
                                <span className="text-2xl font-bold text-blue-700">${product.Price.toFixed(2)}</span>
                                <button 
                                    onClick={() => addToCart(product)}
                                    className="bg-blue-500 text-white px-4 py-2 rounded-lg hover:bg-blue-600 flex items-center space-x-2 transition-colors duration-200"
                                >
                                    <FaShoppingCart />
                                    <span>Add to Cart</span>
                                </button>
                            </div>
                        </div>
                    </div>
                ))}
            </div>
        </div>
    );
}

export default HomePage;