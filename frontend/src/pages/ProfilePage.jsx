import React, { useState, useEffect } from 'react';
import { fetchAuthSession } from 'aws-amplify/auth';
import { FaUser, FaEnvelope, FaMapMarkerAlt } from 'react-icons/fa'; // ไอคอน

const API_ENDPOINT = import.meta.env.VITE_API_ENDPOINT;

function ProfilePage() {
    const [profile, setProfile] = useState(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [isEditing, setIsEditing] = useState(false);
    const [formData, setFormData] = useState({
        FirstName: '',
        LastName: '',
        ShippingAddress: '',
    });

    useEffect(() => {
        const fetchProfile = async () => {
            try {
                setLoading(true);
                setError(null);
                const session = await fetchAuthSession();
                const jwtToken = session.tokens?.idToken?.toString();

                if (!jwtToken) {
                    throw new Error("No IdToken found.");
                }

                const response = await fetch(`${API_ENDPOINT}/profile`, {
                    headers: {
                        Authorization: `Bearer ${jwtToken}`,
                    },
                });

                if (!response.ok) {
                    throw new Error(`HTTP error! status: ${response.status}`);
                }
                const data = await response.json();
                setProfile(data);
                setFormData({
                    FirstName: data.FirstName || '',
                    LastName: data.LastName || '',
                    ShippingAddress: data.ShippingAddress || '',
                });
            } catch (err) {
                console.error("Failed to fetch profile:", err);
                setError("Failed to fetch profile. Please try again.");
            } finally {
                setLoading(false);
            }
        };

        fetchProfile();
    }, []);

    const handleInputChange = (e) => {
        const { name, value } = e.target;
        setFormData(prevData => ({ ...prevData, [name]: value }));
    };

    const handleUpdateProfile = async (e) => {
        e.preventDefault();
        setLoading(true);
        setError(null);

        try {
            const session = await fetchAuthSession();
            const jwtToken = session.tokens?.idToken?.toString();

            if (!jwtToken) {
                throw new Error("No IdToken found.");
            }

            const response = await fetch(`${API_ENDPOINT}/profile`, {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json',
                    Authorization: `Bearer ${jwtToken}`,
                },
                body: JSON.stringify(formData),
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const updatedProfile = await response.json();
            setProfile(updatedProfile);
            setIsEditing(false); // ปิดโหมดแก้ไข
            alert("Profile updated successfully!");
        } catch (err) {
            console.error("Failed to update profile:", err);
            setError("Failed to update profile. Please try again.");
        } finally {
            setLoading(false);
        }
    };

    if (loading) return <div className="text-center text-gray-700">Loading profile...</div>;
    if (error) return <div className="text-center text-red-600">{error}</div>;
    if (!profile) return <div className="text-center text-gray-700">No profile data found.</div>;

    return (
        <div className="p-4 max-w-2xl mx-auto">
            <h1 className="text-3xl font-bold text-gray-800 mb-6 text-center">Your Profile</h1>

            <div className="bg-white rounded-lg shadow-md p-6">
                {isEditing ? (
                    <form onSubmit={handleUpdateProfile} className="space-y-4">
                        <div>
                            <label htmlFor="FirstName" className="block text-gray-700 text-sm font-bold mb-2">First Name:</label>
                            <input
                                type="text"
                                id="FirstName"
                                name="FirstName"
                                value={formData.FirstName}
                                onChange={handleInputChange}
                                className="shadow appearance-none border rounded w-full py-2 px-3 text-gray-700 leading-tight focus:outline-none focus:shadow-outline"
                            />
                        </div>
                        <div>
                            <label htmlFor="LastName" className="block text-gray-700 text-sm font-bold mb-2">Last Name:</label>
                            <input
                                type="text"
                                id="LastName"
                                name="LastName"
                                value={formData.LastName}
                                onChange={handleInputChange}
                                className="shadow appearance-none border rounded w-full py-2 px-3 text-gray-700 leading-tight focus:outline-none focus:shadow-outline"
                            />
                        </div>
                        <div>
                            <label htmlFor="ShippingAddress" className="block text-gray-700 text-sm font-bold mb-2">Shipping Address:</label>
                            <textarea
                                id="ShippingAddress"
                                name="ShippingAddress"
                                value={formData.ShippingAddress}
                                onChange={handleInputChange}
                                rows="3"
                                className="shadow appearance-none border rounded w-full py-2 px-3 text-gray-700 leading-tight focus:outline-none focus:shadow-outline"
                            ></textarea>
                        </div>
                        <div className="flex justify-end space-x-4">
                            <button 
                                type="button" 
                                onClick={() => setIsEditing(false)} 
                                className="bg-gray-300 hover:bg-gray-400 text-gray-800 font-bold py-2 px-4 rounded transition-colors duration-200"
                            >
                                Cancel
                            </button>
                            <button 
                                type="submit" 
                                disabled={loading}
                                className="bg-blue-600 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded transition-colors duration-200 disabled:opacity-50"
                            >
                                {loading ? 'Saving...' : 'Save Changes'}
                            </button>
                        </div>
                    </form>
                ) : (
                    <div className="space-y-4">
                        <p className="flex items-center space-x-2 text-lg"><FaUser className="text-blue-500" /> <span className="font-semibold">Name:</span> {profile.FirstName || 'N/A'} {profile.LastName || ''}</p>
                        <p className="flex items-center space-x-2 text-lg"><FaEnvelope className="text-blue-500" /> <span className="font-semibold">Email:</span> {profile.Email}</p>
                        <p className="flex items-center space-x-2 text-lg"><FaMapMarkerAlt className="text-blue-500" /> <span className="font-semibold">Shipping Address:</span> {profile.ShippingAddress || 'N/A'}</p>
                        <p className="text-sm text-gray-500">Last Updated: {new Date(profile.UpdatedAt).toLocaleString()}</p>
                        <div className="flex justify-end">
                            <button 
                                onClick={() => setIsEditing(true)} 
                                className="bg-blue-500 hover:bg-blue-600 text-white font-bold py-2 px-4 rounded transition-colors duration-200"
                            >
                                Edit Profile
                            </button>
                        </div>
                    </div>
                )}
            </div>
        </div>
    );
}

export default ProfilePage;