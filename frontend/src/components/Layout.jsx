import React from 'react';
import Navbar from './Navbar'; // import Navbar

function Layout({ children }) {
    return (
        <div className="min-h-screen bg-gray-100 flex flex-col">
            <Navbar />
            <main className="flex-grow container mx-auto p-4">
                {children}
            </main>
            {/* อาจจะเพิ่ม Footer ที่นี่ในอนาคต */}
        </div>
    );
}

export default Layout;