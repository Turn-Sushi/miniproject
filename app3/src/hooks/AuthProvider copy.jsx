import React, { createContext, useContext, useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
// import Cookies from 'js-cookie';

export const AuthContext = createContext(null);

export const AuthProvider = ({ children }) => {
    const [isLogin, setIsLogin] = useState(false);
    const [userId, setUserId] = useState(null);
    const navigate = useNavigate();

    useEffect(() => {
        // const token = Cookies.get("accessToken");
        // const storedId = Cookies.get("userUUID");
        if (token && storedId) {
            setIsLogin(true);
            setUserId(storedId);
        }
    }, []);

    const login = (token, userUUID) => {
        // Cookies.set("accessToken", token, { expires: 1 });
        // Cookies.set("userUUID", userUUID, { expires: 1 });
        setIsLogin(true);
        setUserId(userUUID);
    };

    const logout = () => {
        // Cookies.remove("accessToken");
        // Cookies.remove("userUUID");
        setIsLogin(false);
        setUserId(null);
        navigate("/login");
    };

    return (
        <AuthContext.Provider value={{ isLogin, userId, login, logout }}>
            {children}
        </AuthContext.Provider>
    );
};

export const useAuth = () => useContext(AuthContext);
export default AuthProvider;