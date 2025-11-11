import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { Amplify } from 'aws-amplify';
import { withAuthenticator } from '@aws-amplify/ui-react';
import '@aws-amplify/ui-react/styles.css'; // นำเข้าสไตล์ของ Amplify UI
import './App.css'

// Config Amplify
import '../src/contexts/amplifyConfig';

// Layout และ Pages
import Layout from './components/Layout';
import HomePage from './pages/HomePage';
import CartPage from './pages/CartPage';
import ProfilePage from './pages/ProfilePage';

function App({ signOut, user }) { // รับ signOut และ user จาก withAuthenticator
    return (
        <Router>
            <Layout> {/* ห่อหุ้มทุกหน้าด้วย Layout (Navbar + Content) */}
                <Routes>
                    <Route path="/" element={<HomePage />} />
                    <Route path="/cart" element={<CartPage />} />
                    <Route path="/profile" element={<ProfilePage />} />
                    {/* คุณสามารถเพิ่มหน้าอื่นๆ ได้ที่นี่ */}
                </Routes>
            </Layout>
        </Router>
    );
}

// ใช้ withAuthenticator เพื่อจัดการ Login/Logout
const AppWithAuthenticator = withAuthenticator(App, {
    // options
    hideSignUp: false, // สามารถซ่อนปุ่มสมัครสมาชิกได้ถ้าต้องการ
});

export default AppWithAuthenticator;