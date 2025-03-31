import React, { createContext, useState } from "react";
import HomePage from "../components/Home";
import Apage from "../components/Ab";
import Upload from "../components/Upload";

export const NavigationContext = createContext();

export function NavigationProvider({ children }) {
  const [activePage, setActivePage] = useState("home");

  const navigate = (page) => {
    setActivePage(page);
  };

  const getPageComponent = () => {
    switch (activePage) {
      case "about":
        return <Apage />;
      case "upload":
        return <Upload />;
      default:
        return <HomePage />;
    }
  };

  return (
    <NavigationContext.Provider value={{ navigate, getPageComponent }}>
      {children}
    </NavigationContext.Provider>
  );
}
