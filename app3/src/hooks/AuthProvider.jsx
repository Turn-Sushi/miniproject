import React, { createContext, useContext, useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';

export const AuthContext = createContext(null);

export const AuthProvider = ({ children }) => {
    const [isLogin, setIsLogin] = useState(false);
    const [userId, setUserId] = useState(null);
    const navigate = useNavigate();

    useEffect(() => {
        
    }, []);

    const login = (token, userUUID) => {
        setIsLogin(true);
        setUserId(userUUID);
    };

    const logout = () => {
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