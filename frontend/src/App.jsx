import { Amplify } from 'aws-amplify';
import { withAuthenticator } from '@aws-amplify/ui-react';
import '@aws-amplify/ui-react/styles.css';

// (เรา Import Config อีกครั้งที่นี่ เพื่อความแน่ใจ)
// (ไฟล์นี้จะถูก .gitignore)
import './amplifyConfig.js'; 

function App({ signOut, user }) {
  // "signOut" และ "user" ถูกส่งมาจาก withAuthenticator

  return (
    <div className="max-w-xl mx-auto mt-10 p-6 bg-white shadow-md rounded-lg">
      {/* ใช้ Tailwind CSS */}
      <h1 className="text-3xl font-bold text-blue-600 mb-4">
        Hello, {user.username}!
      </h1>
      <p className="text-gray-700 mb-6">
        คุณได้ล็อกอินเข้าสู่ E-commerce PoC ของเราแล้ว
      </p>

      <button 
        onClick={signOut}
        className="w-full bg-red-500 hover:bg-red-700 text-white font-bold py-2 px-4 rounded focus:outline-none focus:shadow-outline"
      >
        Sign Out
      </button>
    </div>
  );
}

// นี่คือ "เวทมนตร์" ครับ
// "withAuthenticator" จะ "ห่อ" App ของเรา
// ถ้า User ยังไม่ล็อกอิน, มันจะแสดงฟอร์ม Login/Sign Up ให้เอง
// ถ้าล็อกอินแล้ว, มันถึงจะแสดง <App /> ของเรา
export default withAuthenticator(App);