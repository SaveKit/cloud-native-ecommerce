import React from 'react';
import { Link } from 'react-router-dom';
import { signOut } from 'aws-amplify/auth';
import { FaShoppingCart, FaUser, FaSignOutAlt } from 'react-icons/fa'; // ไอคอน

function Navbar() {
    const handleSignOut = async () => {
        try {
            await signOut();
            // รีโหลดหน้าเพื่อให้สถานะ Auth ถูกรีเซ็ต (หรือใช้ Context)
            window.location.reload(); 
        } catch (error) {
            console.error("Error signing out:", error);
        }
    };

    return (
        <nav className="bg-blue-600 p-4 text-white shadow-md">
            <div className="container mx-auto flex justify-between items-center">
                <Link to="/" className="text-2xl font-bold">Cloud E-Commerce</Link>
                <div className="flex items-center space-x-6">
                    <Link to="/cart" className="flex items-center space-x-1 hover:text-blue-200">
                        <FaShoppingCart />
                        <span>Cart</span>
                    </Link>
                    <Link to="/profile" className="flex items-center space-x-1 hover:text-blue-200">
                        <FaUser />
                        <span>Profile</span>
                    </Link>
                    <button 
                        onClick={handleSignOut} 
                        className="flex items-center space-x-1 hover:text-blue-200 focus:outline-none"
                    >
                        <FaSignOutAlt />
                        <span>Sign Out</span>
                    </button>
                </div>
            </div>
        </nav>
    );
}

export default Navbar;