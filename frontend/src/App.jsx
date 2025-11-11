import { useState } from 'react';
import { Amplify } from 'aws-amplify';
import { withAuthenticator } from '@aws-amplify/ui-react';
import '@aws-amplify/ui-react/styles.css';
import './amplifyConfig.js'; 

// --- วาง API Endpoint ---
const API_ENDPOINT = import.meta.env.VITE_API_ENDPOINT;

// --- Import "fetchAuthSession" ---
import { fetchAuthSession } from 'aws-amplify/auth'; 

function App({ signOut, user }) {
  // --- State (สถานะ) ---
  const [products, setProducts] = useState([]); // State สำหรับเก็บสินค้า
  const [error, setError] = useState(null);     // State สำหรับเก็บ Error

  const fetchProducts = async () => {
    setError(null); // ล้าง Error เก่า
    setProducts([]); // ล้างรายการสินค้าเก่า

    try {
      // ดึง "กุญแจ" (Session/Token) จาก Amplify
      const session = await fetchAuthSession();
      const idToken = session.tokens?.idToken?.toString(); // ดึง IdToken ออกมา

      if (!idToken) {
        throw new Error("No IdToken found. Please sign in again.");
      }

      // 'fetch' ไปที่ API ของเรา (ที่ล็อคไว้)
      const response = await fetch(`${API_ENDPOINT}/products`, {
        method: 'GET',
        headers: {
          // "แนบกุญแจ" (Token) ไปใน Header!
          'Authorization': `Bearer ${idToken}`
        }
      });

      if (!response.ok) {
        // ถ้า API Gateway ตอบกลับมาว่าไม่ OK (เช่น 500, 404)
        throw new Error(`API call failed with status ${response.status}`);
      }

      const data = await response.json();
      setProducts(data); // บันทึกสินค้าลง State

    } catch (err) {
      console.error("Error fetching products:", err);
      setError(err.message);
    }
  };

  return (
    <div className="max-w-xl mx-auto mt-10 p-6 bg-white shadow-md rounded-lg">
      <h1 className="text-3xl font-bold text-blue-600 mb-4">
        Hello, {user.username}!
      </h1>

      {/* --- เพิ่มปุ่ม และส่วนแสดงผล --- */}
      <button 
        onClick={fetchProducts} // เรียกฟังก์ชัน
        className="w-full bg-blue-500 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded mb-4"
      >
        Fetch Products
      </button>

      {/* แสดงผลลัพธ์ */}
      <div className="mt-4 p-4 bg-gray-50 rounded">
        <h2 className="text-xl font-semibold mb-2">API Response:</h2>
        {error && <pre className="text-red-500">{JSON.stringify(error, null, 2)}</pre>}
        {products.length > 0 ? (
          <pre>{JSON.stringify(products, null, 2)}</pre>
        ) : (
          <p className="text-gray-500">Click button to fetch data...</p>
        )}
      </div>

      <button 
        onClick={signOut}
        className="w-full bg-red-500 hover:bg-red-700 text-white font-bold py-2 px-4 rounded mt-6"
      >
        Sign Out
      </button>
    </div>
  );
}

export default withAuthenticator(App);