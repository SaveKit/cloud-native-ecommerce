// frontend/src/contexts/CartContext.jsx
import React, { createContext, useContext, useState, useEffect } from 'react';

// 1. สร้าง "Context" (กล่องเปล่า)
const CartContext = createContext();

// 2. สร้าง "Provider" (ตัวแจกจ่ายข้อมูล)
export function CartProvider({ children }) {
    // เราจะใช้ useState ที่นี่เป็น "ศูนย์กลาง"
    // เราจะใช้ localStorage เพื่อ "จำ" ตะกร้าไว้ แม้จะปิดเบราว์เซอร์
    const [cartItems, setCartItems] = useState(() => {
        try {
            const localData = localStorage.getItem('cart');
            return localData ? JSON.parse(localData) : [];
        } catch (error) {
            console.error("Could not parse cart from localStorage", error);
            return [];
        }
    });

    // "จำ" ตะกร้าไว้ใน localStorage ทุกครั้งที่ cartItems เปลี่ยน
    useEffect(() => {
        localStorage.setItem('cart', JSON.stringify(cartItems));
    }, [cartItems]);

    // ฟังก์ชัน "เพิ่ม" สินค้า (ที่ HomePage จะเรียกใช้)
    const addToCart = (product) => {
        setCartItems(prevItems => {
            const existingItem = prevItems.find(item => item.product.ProductID === product.ProductID);

            if (existingItem) {
                // ถ้ามีอยู่แล้ว -> เพิ่มจำนวน
                return prevItems.map(item =>
                    item.product.ProductID === product.ProductID
                        ? { ...item, quantity: item.quantity + 1 }
                        : item
                );
            } else {
                // ถ้ายังไม่มี -> เพิ่มเข้าไปใหม่
                return [...prevItems, { product, quantity: 1 }];
            }
        });
        alert(`${product.Name} added to cart!`);
    };

    // ฟังก์ชัน "อัปเดต" (ที่ CartPage จะเรียกใช้)
    const updateQuantity = (productID, delta) => {
        setCartItems(prevItems => {
            return prevItems.map(item =>
                item.product.ProductID === productID
                    ? { ...item, quantity: Math.max(1, item.quantity + delta) } // อย่างน้อย 1 ชิ้น
                    : item
            ).filter(item => item.quantity > 0); // (กรองอันที่น้อยกว่า 1 ทิ้ง)
        });
    };

    // ฟังก์ชัน "ลบ" (ที่ CartPage จะเรียกใช้)
    const removeItem = (productID) => {
        setCartItems(prevItems => prevItems.filter(item => item.product.ProductID !== productID));
    };

    // ฟังก์ชัน "ล้าง" (ที่ CartPage จะเรียกใช้หลัง Checkout)
    const clearCart = () => {
        setCartItems([]);
    };

    // ค่าที่เราจะ "แจกจ่าย" ให้แอปทั้งหมด
    const value = {
        cartItems,
        addToCart,
        updateQuantity,
        removeItem,
        clearCart
    };

    return <CartContext.Provider value={value}>{children}</CartContext.Provider>;
}

// 3. สร้าง "Hook" (ทางลัด)
// เพื่อให้ Component อื่นๆ เรียกใช้ได้ง่าย
export function useCart() {
    return useContext(CartContext);
}